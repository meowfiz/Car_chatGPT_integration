"""straznik_reguly.py -- PURE rule functions of the rules guard (change straznik-regul, D2a).

No I/O, no subprocess, no clock. The same functions run in the window (hook) and in the offline
auditor (tools/straznik_audyt.py), so a number in a report and a decision in a window cannot diverge.
ASCII only (ZASADY 4.1): Polish letters appear as \\u escapes inside regular expressions.

Rules implemented here (catalog D1.1):
  R-GLOS / R-GLOS-TAG   ZASADY 7.6   a [glos] / [glos-X] prompt must get a Glosowo line for device X
  R-PUSH                ZASADY 2.10  unpushed commits older than 30 min (pure verdict; git lives in straznik_git)
  R-STEMPEL             ZASADY 7.8   a turn longer than 2 min starts with [HH:MM] and ends with
                                     [HH:MM->HH:MM . Nm]
"""
import json
import re

WERSJA = "0.1"

TAG_RE = re.compile(r"\[glos(?:-([A-Za-z0-9_]+))?\]")
# the end stamp the owner's measurement counted (no duration part required) and the strict 7.8 form
STAMP_END_LUZNY = re.compile(r"\[\d{1,2}:\d{2}\s*(?:->|\u2192)\s*\d{1,2}:\d{2}")
STAMP_END_SCISLY = re.compile(
    r"\[\d{1,2}:\d{2}\s*(?:->|\u2192)\s*\d{1,2}:\d{2}\s*\u00b7\s*(?:\d+h\s*)?\d{1,2}m\]")
STAMP_START = re.compile(r"^\s*\[\d{1,2}:\d{2}\]")
PROG_STEMPLA_S = 120          # 7.8: "dluzsze niz 2 minuty"
OKNO_TAGU = 400               # the tag is looked for in the first 400 chars of the prompt
OKNO_KONCA = 300              # the end stamp is looked for in the last 300 chars of the last text

_RELEVANT = re.compile(rb'"type"\s*:\s*"(?:user|assistant)"|queued_command')
_SKIP_PREFIXES = (b'{"type":"api-request-blob"', b'{"type":"file-history')


class Tura(object):
    """One user turn: from a real prompt to the next one (transcript view, main session only)."""

    def __init__(self, proj=None, ts=None):
        self.proj = proj
        self.ts = ts                 # epoch seconds of the prompt
        self.end = ts                # epoch seconds of the last assistant entry
        self.glos = False            # the prompt itself carries [glos...]
        self.tag = None              # device id of that tag (None for plain [glos])
        self.texts = []              # assistant text blocks, in order
        self.model = None            # last real model id seen in the turn
        self.interrupted = False
        self.queued_glos = []        # (index into texts at that moment, tag) of queued_command prompts
        self.uuid = None             # uuid of the opening prompt line (None when the transcript has none)
        self.sesja = None            # sessionId of the opening prompt line
        self.idx = None              # index (in the iterable given to tura_z_linii) of the opening line
        self.narzedzia = []          # names of tool_use blocks, in order
        self.prompt = ""             # first OKNO_TAGU chars of the prompt (kept in memory only, never logged)


def parse_ts(s):
    """ISO timestamp with a trailing Z -> epoch seconds, None when unreadable."""
    from datetime import datetime
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def tekst_promptu(msg):
    """Text of a user message; None for tool results (those are not prompts)."""
    c = msg.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
            return None
        return "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
    return None


def tura_z_linii(linie, proj=None):
    """Transcript lines (bytes, str or dict) -> list of Tura, in order.

    A turn is opened by a real user prompt (not a tool result, not meta, not a local command);
    a queued_command attachment with a tag opens an extra obligation inside the running turn.
    """
    tury = []
    cur = None
    for i, raw in enumerate(linie):
        if isinstance(raw, dict):
            d = raw
            raw_b = json.dumps(raw, ensure_ascii=True).encode("ascii")
        else:
            raw_b = raw if isinstance(raw, bytes) else raw.encode("utf-8", "replace")
            if raw_b.startswith(_SKIP_PREFIXES):
                continue
            if _RELEVANT.search(raw_b) is None:       # tolerant of whitespace around the colon
                continue
            try:
                d = json.loads(raw_b)
            except Exception:
                continue
        if not isinstance(d, dict) or d.get("isSidechain"):
            continue
        ts = parse_ts(d["timestamp"]) if d.get("timestamp") else None
        typ = d.get("type")
        if typ == "user" and not d.get("isMeta"):
            txt = tekst_promptu(d.get("message") or {})
            if txt is None or txt.startswith("<local-command") or txt.startswith("<command-") \
                    or txt.startswith("[Request interrupted"):
                if txt and txt.startswith("[Request interrupted") and cur is not None:
                    cur.interrupted = True
                continue
            if cur is not None:
                tury.append(cur)
            cur = Tura(proj, ts)
            cur.uuid = d.get("uuid")
            cur.sesja = d.get("sessionId")
            cur.idx = i
            cur.prompt = txt[:OKNO_TAGU]
            m = TAG_RE.search(txt[:OKNO_TAGU])
            cur.glos = bool(m)
            cur.tag = m.group(1) if m else None
        elif typ == "attachment" or (b"queued_command" in raw_b and typ != "assistant"):
            att = d.get("attachment") or {}
            p = att.get("prompt") if isinstance(att, dict) else None
            if isinstance(p, list):
                p = " ".join(x.get("text", "") for x in p if isinstance(x, dict))
            if cur is not None and isinstance(p, str):
                m = TAG_RE.search(p[:OKNO_TAGU])
                if m:
                    cur.queued_glos.append((len(cur.texts), m.group(1)))
        elif typ == "assistant" and cur is not None:
            msg = d.get("message") or {}
            if msg.get("model") and msg.get("model") != "<synthetic>":
                cur.model = msg.get("model")
            for b in msg.get("content") or []:
                if isinstance(b, dict) and b.get("type") == "text" and b.get("text"):
                    cur.texts.append(b["text"])
                elif isinstance(b, dict) and b.get("type") == "tool_use":
                    cur.narzedzia.append(str(b.get("name") or "?"))
            if ts:
                cur.end = ts
    if cur is not None:
        tury.append(cur)
    return tury


def rodzina_modelu(model):
    m = (model or "?").lower()
    for k in ("opus", "sonnet", "haiku", "fable"):
        if k in m:
            return k
    return m[:20]


# ---- R-GLOS / R-GLOS-TAG (7.6) -----------------------------------------------------------------------------

def linie_glosowo(tekst):
    """Spoken-line tags found in a text: [None, 'dev_ab', ...] -- None for a plain `Glosowo:`.

    Same line identity as cli_bridge._parse_spoken: strip bullets and bold marks, fold the Polish l-stroke,
    case-insensitive; `Glosowo-NAME:` gives NAME (lower case), `Glosowo:` gives None.
    """
    out = []
    for raw in (tekst or "").splitlines():
        norm = raw.strip().lstrip("*_> \u25cf\t").strip()
        head = norm.lower().replace("\u0142", "l")
        if head.startswith("glosowo-") and ":" in head:
            tag = head[len("glosowo-"):head.index(":")].strip()
            if tag and norm[norm.index(":") + 1:].strip(" *_"):   # the relay drops an empty tag or empty text
                out.append(tag)
        elif head.startswith("glosowo:"):
            if norm[len("glosowo:"):].strip(" *_"):
                out.append(None)
    return out


def regula_glos(linie, tag):
    """Verdict for one obligation: 'ok' | 'brak' | 'bez_tagu' | 'zly_tag'.

    linie: result of linie_glosowo over the assistant texts after the obligation opened.
    tag:   device id of the prompt (None for a plain [glos]).
    ok       a line for the asking device (or any line when the prompt had no tag)
    bez_tagu lines exist, none tagged for the device, but a plain `Glosowo:` does (plays everywhere)
    zly_tag  lines exist, all tagged for other devices (will not sound on the asking one)
    brak     no Glosowo line at all
    """
    if not linie:
        return "brak"
    if not tag:
        return "ok"
    t = tag.lower()
    if t in linie:
        return "ok"
    if None in linie:
        return "bez_tagu"
    return "zly_tag"


def zobowiazania_glos(tura):
    """[(wynik, tag)] for every voice obligation of a turn; 'przerwane' for an interrupted turn."""
    ob = []
    if tura.glos:
        ob.append((0, tura.tag))
    ob += list(tura.queued_glos)
    wyniki = []
    for idx, tag in ob:
        if tura.interrupted:
            wyniki.append(("przerwane", tag))
            continue
        linie = [x for txt in tura.texts[idx:] for x in linie_glosowo(txt)]
        wyniki.append((regula_glos(linie, tag), tag))
    return wyniki


def regula_glos_tag(tura):
    """Turn-level verdict of R-GLOS / R-GLOS-TAG: the worst of the turn's obligations.

    'nie_dotyczy' | 'ok' | 'bez_tagu' | 'zly_tag' | 'brak'  (priority brak > zly_tag > bez_tagu > ok).
    An interrupted turn and a turn without a voice tag are 'nie_dotyczy'.
    """
    wyniki = [w for w, _t in zobowiazania_glos(tura) if w != "przerwane"]
    if not wyniki:
        return "nie_dotyczy"
    for gorszy in ("brak", "zly_tag", "bez_tagu"):
        if gorszy in wyniki:
            return gorszy
    return "ok"


_BLOK_KODU = re.compile(r"```.*?```", re.S)
_URL = re.compile(r"https?://\S+")
_SCIEZKA = re.compile(
    r"(?:[A-Za-z]:)?[\\/][\w.\-]+(?:[\\/][\w.\-]+)+"
    r"|\b[\w\-]+\.(?:py|md|json|js|ts|c|cpp|h|txt|jsonl|html)\b")
_HASH = re.compile(r"\b[0-9a-f]{7,40}\b")
_KONCOWKA = re.compile(r"(?<=[.!?])\s+")
MOWA_STALA = "Skonczylem, szczegoly sa w oknie."
MOWA_MAX = 200
MOWA_MIN = 15


def mowa_zastepcza(tekst):
    r"""Substitute spoken text (D5) from the last assistant text: no code, tables, headings, paths, hashes, URLs.

    Takes the first 1-2 sentences (<= 200 chars); when nothing sensible is left, a fixed sentence.
    The result never contains the characters / \ ` # |
    """
    linie = []
    for l in _BLOK_KODU.sub(" ", tekst or "").splitlines():
        l = l.strip()
        if not l or l[0] in "|#[":
            continue
        linie.append(l.lstrip("-*> \t"))
    t = " ".join(linie)
    t = _URL.sub(" ", t)
    t = _SCIEZKA.sub(" ", t)
    t = _HASH.sub(" ", t)
    t = re.sub(r"[`*_]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    zdania = [z for z in _KONCOWKA.split(t) if z.strip()]
    wynik = ""
    for z in zdania[:2]:
        kand = (wynik + " " + z).strip()
        if len(kand) > MOWA_MAX:
            break
        wynik = kand
    if not wynik and zdania:
        wynik = zdania[0][:MOWA_MAX].rstrip()
    wynik = re.sub(r"[/\\`#|]", " ", wynik)
    wynik = re.sub(r"\s+", " ", wynik).strip()
    if len(wynik) < MOWA_MIN or not re.search(r"[^\W\d_]", wynik):
        return MOWA_STALA
    return wynik


# ---- R-STEMPEL (7.8) ---------------------------------------------------------------------------------------

def czas_tury_s(tura):
    return (tura.end or tura.ts or 0) - (tura.ts or 0)


def regula_stempel(tura, prog_s=PROG_STEMPLA_S):
    """Stamp verdict for a turn, or None when the rule does not apply.

    Applies only to a finished (not interrupted) turn with an answer, longer than prog_s seconds.
    Returns {'start': bool, 'koniec': bool, 'koniec_scisly': bool}:
      start          the first text starts with [HH:MM]
      koniec         the last 300 chars hold [HH:MM->HH:MM (loose form, as in the 2026-11-23 baseline)
      koniec_scisly  the full 7.8 form [HH:MM->HH:MM . Nm]
    """
    if tura.model is None or tura.interrupted or tura.ts is None:
        return None
    if czas_tury_s(tura) <= prog_s:
        return None
    ostatni = tura.texts[-1] if tura.texts else ""
    pierwszy = tura.texts[0] if tura.texts else ""
    koniec = ostatni[-OKNO_KONCA:]
    return {"start": bool(STAMP_START.search(pierwszy)),
            "koniec": bool(STAMP_END_LUZNY.search(koniec)),
            "koniec_scisly": bool(STAMP_END_SCISLY.search(koniec))}

# ---- R-PUSH (ZASADY 2.10) ----------------------------------------------------------------------------------

PROG_PUSH_S = 1800            # an unpushed commit older than 30 min is a violation
INTERWAL_OSTRZEZENIA_S = 1800  # one warning per project per 30 min
SPRAWDZ_PUSH_CO_S = 300       # git is asked at most every 5 min per project (a commit must be 30 min old to count)


def parsuj_log_push(wyjscie):
    """Output of `git log --format=%ct @{u}..HEAD` -> (ahead, oldest commit epoch) or None when unreadable.

    One committer timestamp per line; an empty output means nothing unpushed: (0, None).
    """
    if not isinstance(wyjscie, str):
        return None
    ts = []
    for l in wyjscie.splitlines():
        l = l.strip()
        if not l:
            continue
        if not l.isdigit():
            return None
        ts.append(int(l))
    return (len(ts), min(ts)) if ts else (0, None)


def regula_push(ahead, najstarszy_ts, teraz, prog_s=PROG_PUSH_S):
    """'niewypchniety' | 'swiezy' | 'ok'; None when there is no verdict (git error, no upstream).

    niewypchniety  ahead > 0 and the oldest unpushed commit is older than prog_s (strictly)
    swiezy         ahead > 0 but the oldest commit is not older than prog_s
    ok             nothing unpushed
    """
    if ahead is None or not isinstance(ahead, int) or ahead < 0:
        return None
    if ahead == 0:
        return "ok"
    if najstarszy_ts is None:
        return None
    return "niewypchniety" if (teraz - najstarszy_ts) > prog_s else "swiezy"


def czy_ostrzec_push(ostrzezono_ts, teraz, interwal_s=INTERWAL_OSTRZEZENIA_S):
    """True when no warning was given yet or the last one is at least interwal_s old."""
    return not ostrzezono_ts or (teraz - ostrzezono_ts) >= interwal_s


def komunikat_push(ahead, wiek_min):
    """One ASCII line for UserPromptSubmit additionalContext."""
    return ("Masz %d niewypchnietych commitow (najstarszy %d min); wypchnij wg ZASADY 2.10 po bramkach G1-G5"
            % (ahead, wiek_min))


# ---- instruction for the enforced R-GLOS block (Stop) -------------------------------------------------------

def powod_blokady_glos(tag):
    """Reason text returned to the model by a Stop block: add the missing spoken line. ASCII (escapes)."""
    linia = "Glosowo-%s:" % tag if tag else "Glosowo:"
    return ("Polecenie g\u0142osowe wymaga linii mowy (ZASADY 7.6). Dopisz na ko\u0144cu odpowiedzi lini\u0119 \u0027%s ...\u0027: "
            "jedno-dwa zdania po polsku, z polskimi znakami, bez \u015bcie\u017cek i nazw plik\u00f3w, "
            "z bezpo\u015bredni\u0105 odpowiedzi\u0105 lub wynikiem. Nic wi\u0119cej nie zmieniaj."
            % linia)
