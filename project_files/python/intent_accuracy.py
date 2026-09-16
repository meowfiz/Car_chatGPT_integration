"""Accuracy of the intent parser on the utterance fixture (PREREJESTRACJA voice-intent 5.1).

Counts exactly what the pre-registration declared, and nothing else:
    trafienie        repo == oczekiwane
    falszywe         repo is a concrete repository, oczekiwane was a different one or "*"
    uczciwe "*"      repo == "*" and oczekiwane == "*"  (neither a hit nor a false hit)
    przeoczenie      repo == "*" and oczekiwane was a concrete repository

One declared statistic (hit rate) and one safety condition (false hits). ZASADY 6.1: the header
says which files produced the numbers, because a path is not an identity.

Run: python project_files/python/intent_accuracy.py
"""

import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from poc import intent  # noqa: E402

FIXTURE = os.path.join(ROOT, "project_files", "python", "tests", "fixtures",
                       "wypowiedzi.json")


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()[:16]


def git(args):
    try:
        out = subprocess.run(["git"] + args, cwd=ROOT, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=15)
        return out.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return "?"


def provenance():
    dirty = "brudne" if git(["status", "--porcelain"]) else "czyste"
    return [
        "commit %s (%s), drzewo %s" % (git(["rev-parse", "--short", "HEAD"]),
                                       git(["rev-parse", "--abbrev-ref", "HEAD"]), dirty),
        "komenda: python project_files/python/intent_accuracy.py",
        "wejscie: %s sha256:%s" % (os.path.relpath(FIXTURE, ROOT), sha256(FIXTURE)),
        "wejscie: %s sha256:%s" % (os.path.relpath(intent.ALIASES_PATH, ROOT),
                                   sha256(intent.ALIASES_PATH)),
    ]


def run():
    table = intent.load_aliases()
    with open(FIXTURE, "r", encoding="utf-8") as fh:
        rows = json.load(fh)["wypowiedzi"]

    counts = {"trafienie": 0, "falszywe": 0, "uczciwa-gwiazdka": 0, "przeoczenie": 0}
    by_source = {}
    wrong = []
    for row in rows:
        repo, reason = intent.match_repo(row["tekst"], table)
        want = row["oczekiwane"]
        if repo == want:
            kind = "trafienie" if want != "*" else "uczciwa-gwiazdka"
        elif repo == "*":
            kind = "przeoczenie"
        else:
            kind = "falszywe"
        counts[kind] += 1
        slot = by_source.setdefault(row["zrodlo"], {"n": 0, "trafienie": 0, "falszywe": 0})
        slot["n"] += 1
        if kind in slot:
            slot[kind] += 1
        if kind in ("falszywe", "przeoczenie"):
            wrong.append((kind, repo, reason, want, row["tekst"]))

    named = counts["trafienie"] + counts["przeoczenie"] + counts["falszywe"]
    print("PROWENIENCJA")
    for line in provenance():
        print("  " + line)
    print()
    print("Wypowiedzi: %d (z nazwanym projektem: %d)" % (len(rows), named))
    print("  trafienia:        %d" % counts["trafienie"])
    print("  przeoczenia (*):  %d" % counts["przeoczenie"])
    print("  falszywe:         %d" % counts["falszywe"])
    print("  uczciwe * :       %d" % counts["uczciwa-gwiazdka"])
    if named:
        print("TRAFNOSC: %.1f%% (prog hipotezy 80%%, negatyw ponizej 70%%)"
              % (100.0 * counts["trafienie"] / named))
    print("FALSZYWE TRAFIENIA: %.1f%% ze wszystkich (warunek bezpieczenstwa: <= 10%%)"
          % (100.0 * counts["falszywe"] / len(rows)))
    print()
    print("Konfuzja 'zrodlo' (fixture pisany przy biurku jest latwiejszy niz mowa w aucie):")
    for name, slot in sorted(by_source.items()):
        print("  %-12s n=%2d trafien=%2d falszywych=%d" % (name, slot["n"], slot["trafienie"],
                                                           slot["falszywe"]))
    if wrong:
        print()
        print("Niezgodne wiersze:")
        for kind, repo, reason, want, text in wrong:
            print("  [%s] dostalem %s (%s), oczekiwane %s :: %s"
                  % (kind, repo, reason, want, text))
    return 0


if __name__ == "__main__":
    sys.exit(run())
