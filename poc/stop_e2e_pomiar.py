"""Z24 — pomiar e2e /api/car/stop 10 prob z pecetu (symulacja telefonu, user offline).

Procedura wg prerejestracji 2c.10 w tasks.md:
1. Stworz pane 'stop-test' z `sleep 300` jako jedynym procesem.
2. 10 razy: curl POST /api/car/stop {pane: stop-test}, odstepy ~5 s.
   Przed i po: `tmux capture-pane -p` -- zmiana = send-keys zadzialal.
   Nowa sesja po kazdym stopie (bo sleep sam konczy sesje).
3. Zapis jsonl do project_files/run_files/stop_e2e_<data>.jsonl.
4. Dystrybucja: min/median/p90/max latencji, 10/10 skutecznosci, 10/10 HTTP OK.
5. Decyzja wg prerejestracji.
"""
from __future__ import annotations

import json
import os
import ssl
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime


BASE = "https://100.127.128.47:8788"
TOKEN_PATH = os.path.join(os.path.expanduser("~"), ".claude", "car_tokens.json")
PANE = "stop-test"
RUN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "project_files", "run_files")


def read_token():
    with open(TOKEN_PATH, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)["token"]


def tmux(*args, timeout=10):
    """Wrapper na wsl tmux, zwraca (rc, stdout, stderr) jako str."""
    cmd = ["wsl.exe", "-e", "tmux"] + list(args)
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return (p.returncode,
                p.stdout.decode("utf-8", "replace"),
                p.stderr.decode("utf-8", "replace"))
    except subprocess.TimeoutExpired:
        return (-1, "", "timeout")


def create_pane():
    """Idempotentne: zabij ewentualna wczesniejsza sesje, zaloz nowa z sleep."""
    tmux("kill-session", "-t", "=" + PANE + ":")
    time.sleep(0.3)
    rc, _, err = tmux("new-session", "-d", "-s", PANE, "sleep 300")
    if rc != 0:
        raise RuntimeError("new-session failed: " + err)


def capture():
    rc, out, _ = tmux("capture-pane", "-t", "=" + PANE + ":", "-p")
    return out if rc == 0 else ""


def post_stop(token):
    """Jedna proba: wysyla POST, zwraca (status, dt_s, body)."""
    data = json.dumps({"pane": PANE}).encode("utf-8")
    ctx = ssl._create_unverified_context()
    r = urllib.request.Request(BASE + "/api/car/stop", data=data, method="POST",
                               headers={"Authorization": "Bearer " + token,
                                        "Content-Type": "application/json"})
    t0 = time.time()
    try:
        resp = urllib.request.urlopen(r, context=ctx, timeout=5)
        dt = time.time() - t0
        body = json.loads(resp.read().decode("utf-8"))
        return resp.status, dt, body
    except urllib.error.HTTPError as e:
        dt = time.time() - t0
        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            body = {}
        return e.code, dt, body
    except Exception as e:  # noqa: BLE001
        dt = time.time() - t0
        return 0, dt, {"_err": str(e)}


def main(n=10, interval=5.0):
    os.makedirs(RUN_DIR, exist_ok=True)
    out_path = os.path.join(
        RUN_DIR, "stop_e2e_%s.jsonl" % datetime.now().strftime("%Y-%m-%d-%H%M%S"))
    token = read_token()
    rows = []
    print("Z24: pomiar /api/car/stop e2e x%d, interval=%.1fs, pane=%s" %
          (n, interval, PANE))
    print("wynik -> %s" % out_path)
    print()
    for i in range(1, n + 1):
        create_pane()
        time.sleep(0.3)  # tmux session faktycznie wystartowala
        before = capture()
        status, dt, body = post_stop(token)
        time.sleep(0.3)  # send-keys ma czas dojsc
        after = capture()
        changed = (before != after)
        pane_alive = (tmux("has-session", "-t", "=" + PANE + ":")[0] == 0)
        row = {
            "nr": i,
            "ts": datetime.now().isoformat(timespec="seconds"),
            "status": status,
            "dt_ms": round(dt * 1000, 1),
            "outcome": body.get("outcome"),
            "text": body.get("text"),
            "capture_changed": changed,
            "pane_alive_after": pane_alive,
        }
        rows.append(row)
        print("  %2d/%d: HTTP %d, %6.1f ms, outcome=%s, changed=%s, pane_alive=%s" %
              (i, n, status, row["dt_ms"], row["outcome"], changed, pane_alive))
        # Zapis streamowo zeby przy crashu mieliśmy co jest
        with open(out_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        if i < n:
            time.sleep(interval - 0.6)

    # Dystrybucja
    print()
    print("=" * 70)
    latencies_ok = [r["dt_ms"] for r in rows if r["status"] == 200]
    changed_count = sum(1 for r in rows if r["capture_changed"])
    http_ok_count = sum(1 for r in rows if r["status"] == 200)
    print("ZEBRANE: %d prob, zapis w %s" % (len(rows), out_path))
    print()
    print("Miara (1) - latencja e2e [ms] dla HTTP 200:")
    if latencies_ok:
        print("  min    = %.1f" % min(latencies_ok))
        print("  median = %.1f" % statistics.median(latencies_ok))
        print("  p90    = %.1f" % _p90(latencies_ok))
        print("  max    = %.1f" % max(latencies_ok))
        print("  prog MEDIAN <= 1500 ms, p90 <= 2500 ms")
    else:
        print("  (brak probek 200 OK)")
    print()
    print("Miara (2) - skutecznosc send-keys (capture-pane zmiana): %d/%d" %
          (changed_count, len(rows)))
    print("  prog: 10/10")
    print()
    print("Miara (3) - status HTTP 200: %d/%d" % (http_ok_count, len(rows)))
    print("  prog: 10/10")

    # Decyzja
    ok1 = latencies_ok and statistics.median(latencies_ok) <= 1500 and _p90(latencies_ok) <= 2500
    ok2 = changed_count == len(rows)
    ok3 = http_ok_count == len(rows)
    neg = (not latencies_ok) or statistics.median(latencies_ok) > 3000 or http_ok_count < len(rows)
    print()
    if ok1 and ok2 and ok3:
        print("DECYZJA: ZALICZONE (3/3 miary spelnione)")
    elif neg:
        print("DECYZJA: NEGATYW (hipoteza negatywna aktywna) -- wrot do architektury")
    else:
        print("DECYZJA: CZESCIOWE -- nie wszystkie progi spelnione, miara X nie zdala")
    # Posprzataj
    tmux("kill-session", "-t", "=" + PANE + ":")


def _p90(xs):
    s = sorted(xs)
    k = int(0.9 * (len(s) - 1))
    return s[k]


if __name__ == "__main__":
    main()
