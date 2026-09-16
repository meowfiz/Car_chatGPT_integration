"""Intent layer of the voice bridge: free Polish speech -> the structure our machinery speaks.

OpenSpec change voice-intent. ASCII only per ZASADY 4.1 (Polish letters as \\u escapes).

Everything here is a pure function (ZASADY 4.5): text in, dict out. No network, no clock, no
model call - so the whole accuracy measurement is one loop over a fixture, with no server.

Structure, version 1:
    {"v": 1,
     "intent": "ask" | "note" | "queue",
     "repo": "<canonical name>" | "*",
     "repo_reason": "exact" | "fuzzy" | "explicit-all" | "ambiguous" | "no-match",
     "text": "<whole utterance>",
     "limit_zdan": <int> | None}

Only "ask" is executed. "note" and "queue" are recognised and refused out loud, because every
write needs the gates of ZASADY 2.7-2.9, which this bridge does not have.
"""

import difflib
import json
import os
import re

ALIASES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aliases.json")
REPO_MAP_PATH = os.path.join(os.path.expanduser("~"), ".claude", "monitor_repos.env")

# Aliases shorter than this are matched as whole words only, never fuzzily: "ha" or "dom"
# would otherwise collect half the sentence at any sane ratio.
MIN_FUZZY_LEN = 4
# Two repositories this close to each other is not a decision, it is a coin toss -> "*".
AMBIGUITY_MARGIN = 0.02

_PL = {
    "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n",
    "ó": "o", "ś": "s", "ź": "z", "ż": "z",
}
_TRANS = str.maketrans(_PL)

# Keyword -> intent. The list is short on purpose: a phrase that is not clearly a write
# request stays a question, which is the only intent that works today.
_NOTE_WORDS = ("zanotuj", "zapisz notatke", "zapisz w notatkach", "dopisz do notatek",
               "dopisz w notatkach", "zrob notatke", "notatka do")
_QUEUE_WORDS = ("dodaj zadanie", "dodaj do kolejki", "zakolejkuj", "odloz na pozniej",
                "wrzuc do kolejki", "dopisz zadanie", "przypomnij mi zeby")

_NUMERALS = {"jednym": 1, "jednego": 1, "dwoch": 2, "dwu": 2, "dwoma": 2, "trzech": 3,
             "trzema": 3, "czterech": 4, "czterema": 4, "pieciu": 5, "piecioma": 5}
_LIMIT_RE = re.compile(r"\b(jednym|jednego|dwoch|dwu|dwoma|trzech|trzema|czterech|czterema"
                       r"|pieciu|piecioma|\d{1,2})\s+zdani")

_REFUSALS = {
    "note": "Zapisywanie notatek jeszcze nie dziala, wiec nic nie zapisalem.",
    "queue": "Odkladanie zadan jeszcze nie dziala, wiec nic nie dodalem.",
}


def normalize(text):
    """Lowercase, Polish letters to ASCII, everything else to a space.

    Both sides of every comparison go through this, so "Carcha gpt" (a real Whisper output
    from the 2026-09-14 log) and "car chat gpt" become comparable at all.
    """
    if not text:
        return ""
    low = str(text).lower().translate(_TRANS)
    kept = [ch if ("a" <= ch <= "z" or "0" <= ch <= "9") else " " for ch in low]
    return " ".join("".join(kept).split())


def load_aliases(path=ALIASES_PATH):
    with open(path, "r", encoding="utf-8") as fh:
        table = json.load(fh)
    table.setdefault("repos", {})
    table.setdefault("wszystkie", [])
    table.setdefault("min_ratio", 0.82)
    return table


def canonical_names(path=REPO_MAP_PATH):
    """Repository names this machine knows, from the map that fills itself on session_start.

    One source of truth on purpose: a second list in code would drift the day a repo moves.
    A missing map is not an error here - it only means we cannot warn about typos.
    """
    names = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                names.append(line.split("=", 1)[0].strip())
    except OSError:
        return []
    return names


def unknown_aliases(table, names):
    """Alias keys that no repository on this machine answers to - usually a typo in the JSON.

    Reported at startup instead of being dropped silently, because a silently dropped repo
    looks exactly like a parser that cannot recognise it.
    """
    if not names:
        return []
    return sorted(k for k in table.get("repos", {}) if k not in names)


def _ngrams(words, size):
    return [" ".join(words[i:i + size]) for i in range(0, max(0, len(words) - size + 1))]


def _alias_score(alias_norm, words, haystack):
    """Best score of one alias against the utterance: 1.0 for a literal hit, else fuzzy."""
    if not alias_norm:
        return 0.0
    if (" " + alias_norm + " ") in haystack:
        return 1.0
    if len(alias_norm) < MIN_FUZZY_LEN:
        return 0.0
    size = len(alias_norm.split())
    best = 0.0
    for gram in _ngrams(words, size):
        ratio = difflib.SequenceMatcher(None, alias_norm, gram).ratio()
        if ratio > best:
            best = ratio
    return best


def match_repo(text, table):
    """(repo, reason). repo is a canonical name or "*"; reason says WHY, which the log needs.

    "*" means two different things - "the driver asked about everything" (explicit-all) and
    "the rules did not decide" (no-match / ambiguous). Without the reason the accuracy
    measurement of task 5.1 has nothing to count.
    """
    norm = normalize(text)
    if not norm:
        return "*", "no-match"
    words = norm.split()
    haystack = " " + norm + " "

    min_ratio = float(table.get("min_ratio", 0.82))
    for phrase in table.get("wszystkie", []):
        if _alias_score(normalize(phrase), words, haystack) >= min_ratio:
            return "*", "explicit-all"

    scored = []
    for repo, aliases in table.get("repos", {}).items():
        best = 0.0
        for alias in aliases:
            score = _alias_score(normalize(alias), words, haystack)
            if score > best:
                best = score
        if best >= min_ratio:
            scored.append((best, repo))
    if not scored:
        return "*", "no-match"
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    top_score, top_repo = scored[0]
    if len(scored) > 1 and (top_score - scored[1][0]) <= AMBIGUITY_MARGIN:
        return "*", "ambiguous"
    return top_repo, ("exact" if top_score >= 1.0 else "fuzzy")


def parse_limit(text):
    """Sentence count, only when it was actually said as a number.

    "krotko" is deliberately not a number: the default limit of three sentences already lives
    in the driver prompt, and guessing a number from an adverb invents a decision nobody made.
    """
    match = _LIMIT_RE.search(normalize(text))
    if not match:
        return None
    token = match.group(1)
    if token.isdigit():
        value = int(token)
        return value if 1 <= value <= 20 else None
    return _NUMERALS.get(token)


def parse_intent(text):
    norm = normalize(text)
    hits = []
    for word in _NOTE_WORDS:
        at = norm.find(normalize(word))
        if at >= 0:
            hits.append((at, "note"))
    for word in _QUEUE_WORDS:
        at = norm.find(normalize(word))
        if at >= 0:
            hits.append((at, "queue"))
    if not hits:
        return "ask"
    hits.sort()
    return hits[0][1]


def parse(text, table=None):
    table = table if table is not None else load_aliases()
    intent = parse_intent(text)
    repo, reason = match_repo(text, table)
    return {"v": 1, "intent": intent, "repo": repo, "repo_reason": reason,
            "text": (text or "").strip(), "limit_zdan": parse_limit(text)}


def refusal(intent):
    """One spoken sentence for an intent we recognise but do not execute."""
    return _REFUSALS.get(intent, "Tego jeszcze nie potrafie.")


def scope_instruction(parsed):
    """Extra prompt lines carrying the scope and the length, appended to the driver prompt.

    Naming the repository in the answer replaces the confirming question: a wrong hit is heard
    immediately and costs zero extra seconds, while "czy chodzi o X?" doubles the whole loop.
    """
    lines = []
    repo = parsed.get("repo")
    if repo and repo != "*":
        lines.append("Pytanie dotyczy repozytorium %s. Zacznij odpowiedz od jego nazwy." % repo)
    else:
        lines.append("Zakres pytania to wszystkie repozytoria. Zacznij odpowiedz od nazwy tego, "
                     "o ktorym mowisz.")
    limit = parsed.get("limit_zdan")
    if limit:
        lines.append("Odpowiedz w maksymalnie %d zdaniach." % limit)
    return " ".join(lines)
