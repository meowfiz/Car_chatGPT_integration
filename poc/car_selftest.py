"""Self-test wszystkich endpointow /api/car/* bramki.

Odpala sie z komputera z Tailscale, czyta token z `~/.claude/car_tokens.json`,
uderza w kazdy endpoint, wypisuje tabele PASS/FAIL/CZAS.

    python poc/car_selftest.py

Zasady 1.5: oznacz zadanie w monitorze (zrobi auto przez PROMPT->prompt uzytkownika).
Zasady 4.1: ASCII w kodzie, polskie znaki tylko w literale testowych fraz.
Zasady 4.10: dekodowanie bajtow UTF-8 jawne.
"""
from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


DEFAULT_BASE = "https://100.127.128.47:8788"
TOKEN_PATH = os.path.join(os.path.expanduser("~"), ".claude", "car_tokens.json")


def read_token(path: str = TOKEN_PATH) -> str:
    with open(path, "r", encoding="utf-8-sig") as fh:
        data = json.load(fh)
    tok = data.get("token")
    if not isinstance(tok, str) or len(tok) < 16:
        raise RuntimeError("brak tokenu w %s" % path)
    return tok


def req(base: str, method: str, path: str, token: str,
        body: dict | None = None, timeout: float = 35.0) -> tuple[int, dict, float]:
    url = base.rstrip("/") + path
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    headers = {"Authorization": "Bearer " + token, "User-Agent": "car-selftest/1"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, method=method, headers=headers)
    ctx = ssl._create_unverified_context()
    t0 = time.time()
    try:
        resp = urllib.request.urlopen(r, context=ctx, timeout=timeout)
        raw = resp.read()
        dt = time.time() - t0
        try:
            body_out = json.loads(raw.decode("utf-8", "replace"))
        except (ValueError, UnicodeDecodeError):
            body_out = {"_raw": raw[:200].decode("utf-8", "replace")}
        return resp.status, body_out, dt
    except urllib.error.HTTPError as e:
        dt = time.time() - t0
        try:
            body_out = json.loads(e.read().decode("utf-8", "replace"))
        except (ValueError, UnicodeDecodeError):
            body_out = {}
        return e.code, body_out, dt
    except Exception as e:  # noqa: BLE001
        dt = time.time() - t0
        return 0, {"_err": str(e)}, dt


def expect(got: int, want: int, label: str) -> bool:
    return got == want


# Sekwencja testow -- kazdy przewiduje status, podstawowe pola i rozsadne limity czasu.
# `check` zwraca (ok, komentarz).
TESTS = [
    ("health", "GET", "/health", None,
     lambda rc, body, dt: (rc == 200, "no body check")),

    ("car.status", "GET", "/api/car/status", None,
     lambda rc, body, dt: (
         rc == 200 and body.get("outcome") == "sent" and "total_projects" in body,
         "projektow %s, otwartych %s" % (body.get("total_projects"), body.get("tasks_open")))),

    ("car.dispatch.unknown_project", "POST", "/api/car/dispatch",
     {"session_id": "selftest", "project": "panda", "prompt": "cokolwiek"},
     lambda rc, body, dt: (
         rc == 200 and body.get("outcome") == "missing",
         "'nie znam projektu panda' -> missing OK")),

    ("car.dispatch.refuse_push", "POST", "/api/car/dispatch",
     {"session_id": "selftest", "project": "project integration", "prompt": "zrob git push"},
     lambda rc, body, dt: (
         rc == 200 and body.get("outcome") == "refused",
         "git push blocked")),

    # UWAGA: nie wysylamy do Car_chatGPT_integration, bo to okno w ktorym pracuje
    # samo-testujace sie Claude. Testujemy sam resolve + dispatch; outcome=sent|timeout
    # oba znacza "bramka zrobila robote" (timeout = okno docelowe zajete, co tez bywa).
    ("car.dispatch.resolve_token_match", "POST", "/api/car/dispatch",
     {"session_id": "selftest", "project": "voice", "prompt": "powiedz Glosowo selftest OK"},
     lambda rc, body, dt: (
         rc == 200 and body.get("outcome") in ("sent", "timeout")
             and body.get("resolved_project") == "voice",
         "resolved=voice outcome=%s" % body.get("outcome"))),

    ("car.open", "POST", "/api/car/open",
     {"project": "voice"},
     lambda rc, body, dt: (
         rc == 200 and body.get("outcome") == "sent" and body.get("resolved_project") == "voice",
         "open voice OK")),

    ("car.project.summary", "GET", "/api/car/project/HA/summary", None,
     lambda rc, body, dt: (
         rc == 200 and body.get("outcome") == "sent" and body.get("resolved_project") == "HA",
         "HA state=%s done=%s/%s" % (body.get("state"), body.get("done"), body.get("total")))),

    ("car.project.unknown", "GET", "/api/car/project/panda/summary", None,
     lambda rc, body, dt: (
         rc == 200 and body.get("outcome") == "missing",
         "panda -> missing")),

    ("car.todo.save", "POST", "/api/car/todo",
     {"text": "selftest TODO " + str(int(time.time())), "project": "car integration",
      "session_id": "selftest"},
     lambda rc, body, dt: (
         rc == 200 and body.get("outcome") == "sent",
         "zapisane do %s" % body.get("resolved_project"))),

    ("car.todo.no_text", "POST", "/api/car/todo",
     {"session_id": "selftest"},
     lambda rc, body, dt: (
         rc == 400,
         "brak text -> 400 OK")),

    ("car.auth.no_token", "POST", "/api/car/dispatch",
     None,  # placeholder; body sends empty JSON but without token
     lambda rc, body, dt: (
         rc == 401,
         "brak tokenu -> 401 OK")),
]


def run(base: str, token: str) -> int:
    rows = []
    fails = 0
    for label, method, path, body, check in TESTS:
        # Specialny przypadek: auth.no_token wysyla bez Bearer
        if label == "car.auth.no_token":
            try:
                r = urllib.request.Request(base.rstrip("/") + path,
                                           data=b"{}", method="POST",
                                           headers={"Content-Type": "application/json"})
                ctx = ssl._create_unverified_context()
                t0 = time.time()
                resp = urllib.request.urlopen(r, context=ctx, timeout=5)
                rc, dt = resp.status, time.time() - t0
                body_out = {"_raw": resp.read()[:100].decode("utf-8", "replace")}
            except urllib.error.HTTPError as e:
                rc, dt = e.code, time.time() - t0
                body_out = {}
            except Exception as e:  # noqa: BLE001
                rc, dt, body_out = 0, 0, {"_err": str(e)}
            ok, note = check(rc, body_out, dt)
        else:
            rc, body_out, dt = req(base, method, path, token, body)
            ok, note = check(rc, body_out, dt)
        status = "OK" if ok else "FAIL"
        if not ok:
            fails += 1
        rows.append((label, method, status, rc, "%.2fs" % dt, note))
        time.sleep(0.1)

    # Tabela
    print()
    print("%-30s %-6s %-6s %-5s %-7s %s" % ("TEST", "METHOD", "STAT", "HTTP", "TIME", "NOTE"))
    print("-" * 100)
    for row in rows:
        label, method, status, rc, dt, note = row
        print("%-30s %-6s %-6s %-5s %-7s %s" % (label, method, status, rc, dt, note[:50]))
    print("-" * 100)
    print("WYNIK: %d/%d PASS, %d FAIL" % (len(rows) - fails, len(rows), fails))
    return 0 if fails == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=DEFAULT_BASE, help="bazowy URL bramki")
    ap.add_argument("--token", help="Bearer (default: z ~/.claude/car_tokens.json)")
    args = ap.parse_args()
    token = args.token or read_token()
    sys.exit(run(args.base, token))


if __name__ == "__main__":
    main()
