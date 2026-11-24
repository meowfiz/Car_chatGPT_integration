#!/usr/bin/env python3
"""straznik_regul.py -- Claude Code hook of the rules guard, change straznik-regul.

    python monitor/straznik_regul.py --hook stop|prompt     (hook JSON on stdin)

Contract:
  - exit code ALWAYS 0; every exception is swallowed and appended to <dir>/bledy.log (no prompt or answer text);
  - stdout stays EMPTY except for two documented cases, both a single JSON object:
      (1) Stop, R-GLOS enforced (mode "wymuszaj"): {"decision":"block","reason":...} when the turn that just ended
          answered a [glos] / [glos-X] prompt with no spoken line (verdict brak) or only lines for other devices
          (zly_tag). NEVER when stop_hook_active is true (the retry after a block is never blocked: no loop).
      (2) UserPromptSubmit, R-PUSH: {"hookSpecificOutput":{"hookEventName":"UserPromptSubmit",
          "additionalContext": "<one line>"}} when unpushed commits are older than 30 min; at most once per
          30 min per project. R-PUSH never blocks anything.
  - a hard wall-clock limit (HARD_LIMIT_S) ends the process even when a read hangs;
  - the registry <dir>/rejestr-YYYY-MM-DD.jsonl holds identifiers and verdicts only, NEVER message text;
  - modes per rule, set in DOMYSLNE / <cwd>/.claude/straznik.json: "loguj" (record only), "wymuszaj"
    (only R-GLOS acts; every other rule is log-only whatever its mode), "wylaczony". An unknown mode is "loguj".
    A project-level {"tryb": X} applies to every rule the project file does not name itself.
  - kill switch: env STRAZNIK_OFF=1 or the file <dir>/WYLACZ; per project {"tryb": "wylaczony"}.
  - R-PUSH asks git (read only, 1 s timeout, in straznik_git.py) at most every 5 min per project.
  - to remove the guard: delete the two hook entries from .claude/settings.json.

<dir> = ~/.claude/straznik (override: env STRAZNIK_DIR, used by the tests).
Stdin is read as bytes and decoded as UTF-8 (ZASADY 4.10). Standard library only. ASCII only.
"""
import json
import os
import socket
import sys
import threading
import time

_T0 = time.perf_counter()
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import straznik_reguly as R  # noqa: E402

WERSJA = R.WERSJA
HARD_LIMIT_S = 2.5            # the hook timeout in settings.json is 3 s
BUDZET_MS = 250               # rules still pending after this are skipped and recorded
TAIL_BYTES = 512 * 1024       # transcript tail read at Stop
STAN_TTL_S = 7 * 86400

TRYBY = ("loguj", "wymuszaj", "wylaczony")
PUSH_BUDZET_MS = 1000         # R-PUSH is skipped when the hook already spent this much

# Canonical defaults; config/straznik_domyslny.json must be equal (test). Only R-GLOS is enforced.
DOMYSLNE = {
    "wersja": "0.2",
    "tryb_globalny": "loguj",
    "reguly": {
        "R-GLOS": {"tryb": "wymuszaj"},
        "R-GLOS-TAG": {"tryb": "loguj"},
        "R-PUSH": {"tryb": "loguj"},
    },
}


def katalog():
    return os.environ.get("STRAZNIK_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "straznik")


def zapisz_blad(kat, hook, exc):
    """One line, no content: time, hook, exception type and message."""
    try:
        os.makedirs(kat, exist_ok=True)
        with open(os.path.join(kat, "bledy.log"), "a", encoding="utf-8") as fh:
            fh.write("%s %s %s: %s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"), hook, type(exc).__name__,
                                         str(exc)[:200].replace("\n", " ")))
    except Exception:
        pass


# ---- configuration -------------------------------------------------------------------------------

def laduj_konfiguracje(cwd):
    """DOMYSLNE merged with <cwd>/.claude/straznik.json (project overrides). Unreadable file -> defaults."""
    cfg = json.loads(json.dumps(DOMYSLNE))
    try:
        p = os.path.join(cwd or "", ".claude", "straznik.json")
        if cwd and os.path.isfile(p):
            with open(p, "rb") as fh:
                over = json.loads(fh.read().decode("utf-8", "replace"))
            if isinstance(over, dict):
                if "tryb" in over:
                    cfg["tryb_globalny"] = over["tryb"]
                    # a project-wide mode also covers the rules the project file does not name itself
                    nazwane = over.get("reguly") or {}
                    for k in cfg["reguly"]:
                        if k not in nazwane:
                            cfg["reguly"][k]["tryb"] = over["tryb"]
                for k, v in (over.get("reguly") or {}).items():
                    if isinstance(v, dict):
                        cfg["reguly"].setdefault(k, {}).update(v)
    except Exception:
        pass
    return cfg


def efektywny_tryb(cfg, regula):
    """'wylaczony' | 'loguj' | 'wymuszaj'. Off anywhere (rule or global) wins; else the rule's own mode, else the
    global one; anything unknown is 'loguj' (fail-safe: no action)."""
    r = (cfg.get("reguly") or {}).get(regula, {})
    if r.get("tryb") == "wylaczony" or cfg.get("tryb_globalny") == "wylaczony":
        return "wylaczony"
    for tryb in (r.get("tryb"), cfg.get("tryb_globalny")):
        if tryb in TRYBY:
            return tryb
    return "loguj"


def wylaczony(kat):
    return os.environ.get("STRAZNIK_OFF") == "1" or os.path.exists(os.path.join(kat, "WYLACZ"))


# ---- transcript tail -----------------------------------------------------------------------------

def ogon_transkryptu(path, max_bytes=TAIL_BYTES):
    """Last complete lines of a transcript, as bytes; at most max_bytes from the end. [] when unreadable."""
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            start = max(0, size - max_bytes)
            fh.seek(start)
            data = fh.read()
    except OSError:
        return []
    linie = data.split(b"\n")
    if start > 0 and linie:
        linie = linie[1:]            # the first line is cut in the middle
    return [l for l in linie if l.strip()]


# ---- state per session ---------------------------------------------------------------------------

def sciezka_stanu(kat, sesja):
    bezp = "".join(c for c in str(sesja or "brak") if c.isalnum() or c in "-_")[:80] or "brak"
    return os.path.join(kat, "stan", bezp + ".json")


def czytaj_stan(kat, sesja):
    try:
        with open(sciezka_stanu(kat, sesja), "rb") as fh:
            d = json.loads(fh.read().decode("utf-8", "replace"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def zapisz_stan(kat, sesja, stan):
    p = sciezka_stanu(kat, sesja)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(stan, ensure_ascii=True))
    os.replace(tmp, p)


def sciezka_stanu_push(kat, cwd):
    import hashlib
    h = hashlib.sha1(os.path.normcase(os.path.abspath(cwd or "")).encode("utf-8", "replace")).hexdigest()[:12]
    return os.path.join(kat, "stan", "push-" + h + ".json")


def czytaj_json(p):
    try:
        with open(p, "rb") as fh:
            d = json.loads(fh.read().decode("utf-8", "replace"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def zapisz_json(p, d):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(d, ensure_ascii=True))
    os.replace(tmp, p)


def sprzatnij_stany(kat, teraz):
    """Drop state files older than STAN_TTL_S (cheap: a directory listing)."""
    d = os.path.join(kat, "stan")
    try:
        for n in os.listdir(d):
            p = os.path.join(d, n)
            if teraz - os.path.getmtime(p) > STAN_TTL_S:
                os.remove(p)
    except OSError:
        pass


# ---- registry ------------------------------------------------------------------------------------

def dopisz_rejestr(kat, rekordy):
    if not rekordy:
        return
    os.makedirs(kat, exist_ok=True)
    p = os.path.join(kat, "rejestr-%s.jsonl" % time.strftime("%Y-%m-%d"))
    with open(p, "a", encoding="utf-8") as fh:
        for r in rekordy:
            fh.write(json.dumps(r, ensure_ascii=True, sort_keys=True) + "\n")


def rekord(hook, regula, **pola):
    r = {"ts": round(time.time(), 3), "maszyna": socket.gethostname(), "wersja": WERSJA, "tryb": "loguj",
         "akcja": "log", "regula": regula, "hook": hook}
    r.update(pola)
    return r


# ---- hooks ---------------------------------------------------------------------------------------

def sprawdz_push(kat, cwd, projekt, sesja, teraz):
    """Stop: R-PUSH. Asks git at most every SPRAWDZ_PUSH_CO_S per project; returns registry records."""
    if not cwd:
        return []
    sp = sciezka_stanu_push(kat, cwd)
    st = czytaj_json(sp)
    if teraz - (st.get("sprawdzono") or 0) < R.SPRAWDZ_PUSH_CO_S:
        return []
    if (time.perf_counter() - _T0) * 1000 > PUSH_BUDZET_MS:
        return []
    import straznik_git as G
    w = G.unpushed(cwd)
    st["sprawdzono"] = teraz
    st["ahead"], st["najstarszy"] = (w if w else (None, None))
    zapisz_json(sp, st)
    if w is None:
        return []
    werdykt = R.regula_push(w[0], w[1], teraz)
    if werdykt not in ("ok", "niewypchniety"):
        return []
    return [rekord("stop", "R-PUSH", projekt=projekt, sesja=sesja, szczegol=werdykt, dotyczy=True,
                   ok=werdykt == "ok", ahead=w[0],
                   wiek_min=int((teraz - w[1]) // 60) if w[1] else 0)]


def ostrzezenie_push(kat, cwd, projekt, sesja, teraz):
    """UserPromptSubmit: (records, message|None). Warns at most once per R.INTERWAL_OSTRZEZENIA_S per project and
    only after git confirms the commits are still unpushed (the state may be stale: auto_sync may have pushed)."""
    if not cwd:
        return [], None
    sp = sciezka_stanu_push(kat, cwd)
    st = czytaj_json(sp)
    if not st.get("ahead") or st.get("najstarszy") is None:
        return [], None
    if R.regula_push(st["ahead"], st["najstarszy"], teraz) != "niewypchniety":
        return [], None
    if not R.czy_ostrzec_push(st.get("ostrzezono"), teraz):
        return [], None
    import straznik_git as G
    w = G.unpushed(cwd)
    if w is None:
        return [], None
    st["ahead"], st["najstarszy"] = w
    if R.regula_push(w[0], w[1], teraz) != "niewypchniety":
        zapisz_json(sp, st)
        return [], None
    st["ostrzezono"] = teraz
    zapisz_json(sp, st)
    wiek = int((teraz - w[1]) // 60)
    rek = rekord("prompt", "R-PUSH", projekt=projekt, sesja=sesja, szczegol="niewypchniety", dotyczy=True,
                 ok=False, ahead=w[0], wiek_min=wiek, akcja="ostrzezenie")
    return [rek], R.komunikat_push(w[0], wiek)


def hook_prompt(dane, kat, cfg, projekt, wyjscie=None):
    """UserPromptSubmit: remember the turn start and the voice tag; log that an obligation opened;
    R-PUSH reminder (additionalContext) when unpushed commits are old."""
    prompt = dane.get("prompt")
    prompt = prompt if isinstance(prompt, str) else ""
    sesja = dane.get("session_id")
    m = R.TAG_RE.search(prompt[:R.OKNO_TAGU])
    zapisz_stan(kat, sesja, {"t0": time.time(), "glos": bool(m), "tag": m.group(1) if m else None,
                             "prompt_id": dane.get("prompt_id")})
    sprzatnij_stany(kat, time.time())
    rek = []
    if m and efektywny_tryb(cfg, "R-GLOS") != "wylaczony":
        rek.append(rekord("prompt", "R-GLOS", projekt=projekt, sesja=sesja, tag=m.group(1),
                          dotyczy=True, ok=None, zdarzenie="otwarte"))
    if efektywny_tryb(cfg, "R-PUSH") != "wylaczony":
        try:
            cwd = dane.get("cwd") if isinstance(dane.get("cwd"), str) else ""
            r2, msg = ostrzezenie_push(kat, cwd, projekt, sesja, time.time())
            rek += r2
            if msg and wyjscie is not None:
                wyjscie.append({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                                       "additionalContext": msg}})
        except Exception as exc:
            zapisz_blad(kat, "prompt-push", exc)
    return rek


def tura_ze_stopu(dane, stan):
    """The turn that just ended, from the transcript tail plus the Stop fields; None when there is none."""
    tp = dane.get("transcript_path")
    linie = ogon_transkryptu(tp) if isinstance(tp, str) else []
    tury = R.tura_z_linii(linie)
    if not tury and stan.get("glos"):
        # a long turn: the opening prompt is out of the tail window; rebuild it from the UPS state
        sztuczny = {"type": "user", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z",
                                                                  time.gmtime(stan.get("t0") or time.time())),
                    "message": {"content": "[glos%s]" % ("-" + stan["tag"] if stan.get("tag") else "")}}
        tury = R.tura_z_linii([sztuczny] + linie)
    if not tury:
        return None
    t = tury[-1]
    ostatnia = dane.get("last_assistant_message")
    if isinstance(ostatnia, str) and ostatnia and (not t.texts or t.texts[-1] != ostatnia):
        t.texts.append(ostatnia)         # the Stop field is the freshest source of the final text
    if t.model is None:
        t.model = "?"
    return t


def stop_glos(dane, kat, cfg, projekt, wyjscie):
    """R-GLOS / R-GLOS-TAG on the turn that just ended: records, and a block when enforced."""
    sesja = dane.get("session_id")
    stan = czytaj_stan(kat, sesja)
    t = tura_ze_stopu(dane, stan)
    rek = []
    if t is None:
        return rek
    if (time.perf_counter() - _T0) * 1000 > BUDZET_MS:
        return [rekord("stop", "R-GLOS", projekt=projekt, sesja=sesja, pominieta="budzet")]
    aktywny = bool(dane.get("stop_hook_active"))
    wspolne = {"projekt": projekt, "sesja": sesja, "tura_uuid": t.uuid, "model": R.rodzina_modelu(t.model),
               "stop_hook_active": aktywny}
    tryb_glos = efektywny_tryb(cfg, "R-GLOS")
    zablokowano = False
    for nr, (wynik, tag) in enumerate(R.zobowiazania_glos(t)):
        if wynik == "przerwane":
            continue
        if tryb_glos != "wylaczony":
            pola = {"tryb": tryb_glos}
            if wynik in ("brak", "zly_tag") and tryb_glos == "wymuszaj":
                if aktywny:
                    pola["blokada_pominieta"] = "stop_hook_active"   # the retry after a block is never blocked
                elif not zablokowano and wyjscie is not None:
                    wyjscie.append({"decision": "block", "reason": R.powod_blokady_glos(tag)})
                    zablokowano = True
                    pola["akcja"] = "blokada"
            rek.append(rekord("stop", "R-GLOS", ob=nr, tag=tag, szczegol=wynik, dotyczy=True,
                              ok=wynik != "brak", **dict(wspolne, **pola)))
        if tag and wynik != "brak" and efektywny_tryb(cfg, "R-GLOS-TAG") != "wylaczony":
            rek.append(rekord("stop", "R-GLOS-TAG", ob=nr, tag=tag, szczegol=wynik, dotyczy=True,
                              ok=wynik == "ok", **wspolne))
    return rek


def hook_stop(dane, kat, cfg, projekt, wyjscie=None):
    """Stop: R-GLOS (+ block when enforced) and R-PUSH (log only). A failure of one never loses the other."""
    rek = stop_glos(dane, kat, cfg, projekt, wyjscie)
    if efektywny_tryb(cfg, "R-PUSH") != "wylaczony":
        try:
            cwd = dane.get("cwd") if isinstance(dane.get("cwd"), str) else ""
            rek += sprawdz_push(kat, cwd, projekt, dane.get("session_id"), time.time())
        except Exception as exc:
            zapisz_blad(kat, "stop-push", exc)
    return rek


HOOKI = {"stop": hook_stop, "prompt": hook_prompt}


def uruchom(nazwa, stdin_bytes, kat=None, wyjscie=None):
    """Whole hook body, fail-open. Returns the number of registry records written (0 on any failure).
    A hook that must answer the CLI appends one JSON object to `wyjscie` (the caller prints it)."""
    kat = kat or katalog()
    try:
        if wylaczony(kat) or nazwa not in HOOKI:
            return 0
        dane = json.loads(stdin_bytes.decode("utf-8", "replace") or "{}")
        if not isinstance(dane, dict):
            return 0
        cwd = dane.get("cwd") if isinstance(dane.get("cwd"), str) else ""
        cfg = laduj_konfiguracje(cwd)
        if cfg.get("tryb_globalny") == "wylaczony":
            return 0
        projekt = os.path.basename(cwd.rstrip("/\\")) if cwd else "?"
        rek = HOOKI[nazwa](dane, kat, cfg, projekt, wyjscie)
        ms = round((time.perf_counter() - _T0) * 1000, 1)
        for r in rek:
            r["ms"] = ms
        dopisz_rejestr(kat, rek)
        return len(rek)
    except Exception as exc:       # fail-open: a guard error must never reach the window
        zapisz_blad(kat, nazwa, exc)
        return 0


def main(argv):
    nazwa = argv[argv.index("--hook") + 1] if "--hook" in argv and argv.index("--hook") + 1 < len(argv) else ""
    # hard wall-clock limit: even a hung read ends the process with exit code 0
    wd = threading.Timer(HARD_LIMIT_S, lambda: os._exit(0))
    wd.daemon = True
    wd.start()
    try:
        try:
            data = sys.stdin.buffer.read()
        except Exception:
            data = b""
        wyj = []
        uruchom(nazwa, data, wyjscie=wyj)
        if wyj:
            sys.stdout.write(json.dumps(wyj[0], ensure_ascii=True))
            sys.stdout.flush()
    except BaseException:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
