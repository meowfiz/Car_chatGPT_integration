"""Does a recognised repository shorten the answer? (PREREJESTRACJA voice-intent 5.2)

Five questions, each asked twice with the SAME wording: once with the scope narrowed to the
recognised repository, once with every repository (today's behaviour). The order inside a pair
alternates, so a warm first call cannot dress up one variant.

One declared statistic: median of the full call. Negative condition: the median does not drop
-> narrowing stays (it still prevents answers from the wrong tree) but MUST NOT be called a
speed-up. Voice and repository sync are excluded here on purpose - they are identical in both
variants and already measured (2,1 s and 1,95 s).

Run: set ASK_SECRET first (any value; nothing is served), then
     python project_files/python/intent_scope_time.py
"""

import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("ASK_SECRET", "pomiar")
os.environ.setdefault("ASK_SYNC", "0")

from poc import ask_server, intent  # noqa: E402

PYTANIA = [
    "Ile zadan zostalo w projekcie Car chat gpt i co jest nastepne",
    "Kiedy byla ostatnia sesja w home assistant",
    "Co slychac w project integration, w dwoch zdaniach",
    "Ile otwartych zadan ma ribnikster",
    "Co nowego w nihongo no sensei",
]


def one(question, narrowed):
    parsed = intent.parse(question, ask_server.ALIASES)
    dirs, scope = ask_server.repos_for(parsed["repo"] if narrowed else "*")
    started = time.time()
    try:
        answer = ask_server.ask_claude(question, dirs,
                                       intent.scope_instruction(dict(parsed, repo=scope)))
        ok = bool(answer.strip())
    except Exception as exc:                       # noqa: BLE001 - a failed call is a datum
        answer, ok = str(exc)[:120], False
    return time.time() - started, scope, ok, ask_server.for_speech(answer)[:110]


def main():
    print("repozytoria: %s" % ", ".join(os.path.basename(p) for p in ask_server.REPOS))
    rows = []
    for i, question in enumerate(PYTANIA):
        order = ["zawezony", "wszystkie"] if i % 2 == 0 else ["wszystkie", "zawezony"]
        for variant in order:
            secs, scope, ok, answer = one(question, variant == "zawezony")
            rows.append((variant, secs, ok))
            print("[%d/%d] %-10s %5.1f s  zakres=%-24s ok=%s :: %s"
                  % (len(rows), 2 * len(PYTANIA), variant, secs, scope, ok, answer))
            sys.stdout.flush()
    print()
    for variant in ("zawezony", "wszystkie"):
        times = [s for v, s, ok in rows if v == variant and ok]
        if times:
            print("%-10s n=%d mediana %.1f s  min %.1f  max %.1f"
                  % (variant, len(times), statistics.median(times), min(times), max(times)))
        else:
            print("%-10s brak udanych wywolan" % variant)
    return 0


if __name__ == "__main__":
    sys.exit(main())
