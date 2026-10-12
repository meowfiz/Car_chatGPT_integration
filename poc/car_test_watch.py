"""Watcher PoC 1.3 — pomiar prób „Hey Siri, CarPlay audio test" bez wracania do komputera.

Odpala sie na maszynie z bramka glosowa (albo przez ssh / RDP), tailuje
`project_integration/project_files/run_files/voice_gateway.log`, laczy pary HIT+OK
z `kind=car-poc` i pokazuje liczby na zywo:

  nr   czas lokalny   remote           dt [s]   ctype       status
  1    14:03:22       100.64.17.3      0.19     audio/wav   ok
  2    14:03:38       100.64.17.3      0.21     audio/wav   ok
  3    14:03:51       100.64.17.3      0.18     audio/wav   ok

Interpretacja:
- 3 wiersze w ciagu ~1 min → Shortcut dotarl 3 razy do serwera. Zostaje odpowiedziec
  „zagralo w aucie czy nie" (serwer tego nie wie).
- 2 wiersze zamiast 3 → jedna proba nie dotarla do serwera (Siri nie zrozumiala /
  LTE padlo / Shortcut sie powiesil).
- `remote` z adresu 100.x.y.z (Tailscale) potwierdza, ze telefon ciagnie przez tailnet.
- `dt` > 5 s → VCC/HA zimne, przy pierwszej probie normalne; przy kolejnych nie.

Argumenty:
  --n N       spodziewana liczba prob (domyslnie 3); po osiagnieciu podsumowanie i exit
  --since S   ignoruj wpisy starsze niz S sekund od startu (domyslnie 60); eliminuje
              smietnik z poprzednich dni
  --log PATH  nadpisanie sciezki logu (test, inna maszyna)
  --json      zamiast tabeli wypisuj po jednym JSONie na linie (do dalszego pomiaru)

Stdlib only. Dziala rowniez pod Windows (plik otwarty do odczytu, nowe linie dopisywane
przez bramke sa widoczne po flush -- bramka woluje `fh.flush()` po kazdym `log()`).

Zasady 1.5: nadaje nazwe zadaniu na starcie, zeby monitor pokazal na telefonie, ze teraz
mierzymy.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

DEFAULT_LOG = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "project_integration", "project_files", "run_files", "voice_gateway.log",
)

HIT_RE = re.compile(r"^(?P<ts>\S+) car-poc test-audio HIT ua=(?P<ua>.+?) remote=(?P<rem>\S+)")
OK_RE  = re.compile(r"^(?P<ts>\S+) car-poc test-audio OK dt=(?P<dt>\S+) ctype=(?P<ct>\S+)")


def parse_ts(s: str) -> float:
    """ISO 8601 UTC -> unix seconds. Bramka pisze z `isoformat(timespec='seconds')`, czyli
    bez mikrosekund i strefa jako `+00:00`. Trzymamy sie tego formatu dokladnie."""
    return datetime.fromisoformat(s).timestamp()


def tail(path: str, since_ts: float):
    """Generator linii dopisywanych do pliku logu. Startuje od konca pliku; przy rotacji
    (plik skasowany / zastapiony) wraca na poczatek nowego pliku.

    `since_ts` filtruje wpisy historyczne: zalozenie — pomiar startuje teraz, cokolwiek
    starsze niz `--since` sekund przed startem to resztka z poprzednich dni."""
    cutoff = time.time() - since_ts
    while True:
        try:
            fh = open(path, "r", encoding="utf-8")
            break
        except FileNotFoundError:
            time.sleep(0.5)
    # Start od konca, zeby nie czytac 100 KB historii; akceptujemy, ze stare wpisy ida
    # tylko przez trafienie przy pierwszym cyklu read_line, jesli jest tam niedoczytany bufor.
    fh.seek(0, os.SEEK_END)
    inode = os.fstat(fh.fileno()).st_ino if hasattr(os, "fstat") else None
    while True:
        line = fh.readline()
        if line:
            line = line.rstrip("\n")
            # Filtr czasu: parsujemy ts z poczatku linii, jesli jest.
            try:
                head = line.split(" ", 1)[0]
                if parse_ts(head) < cutoff:
                    continue
            except (ValueError, IndexError):
                pass
            yield line
            continue
        # EOF — czekamy, albo przeladowujemy przy rotacji.
        time.sleep(0.3)
        try:
            st = os.stat(path)
            if inode is not None and st.st_ino != inode:
                fh.close()
                fh = open(path, "r", encoding="utf-8")
                inode = os.fstat(fh.fileno()).st_ino
        except FileNotFoundError:
            time.sleep(0.5)


def fmt_local(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    ap.add_argument("--n", type=int, default=3, help="spodziewana liczba prob")
    ap.add_argument("--since", type=int, default=60,
                    help="ignoruj wpisy starsze niz N sekund od teraz")
    ap.add_argument("--log", default=DEFAULT_LOG, help="sciezka do voice_gateway.log")
    ap.add_argument("--json", action="store_true", help="JSON po linii zamiast tabeli")
    ap.add_argument("--no-label", action="store_true",
                    help="nie wysylaj etykiety zadania do monitora (do testow)")
    args = ap.parse_args(argv)

    log_path = os.path.abspath(args.log)
    print("watcher: log=%s n=%d since=%ds" % (log_path, args.n, args.since))
    if not args.json:
        print()
        print("  nr  czas       remote          dt     ctype       status")
        print("  --  --------   -------------   ----   ---------   ------")

    # Zasady 1.5: nadaj nazwe zadaniu na starcie — zeby monitor pokazal na telefonie
    # "pomiar CarPlay audio PoC", a nie pierwsze slowa z promptu.
    if not args.no_label:
        try:
            hb = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "..", "monitor", "heartbeat.py")
            if os.path.exists(hb):
                import subprocess
                subprocess.run([sys.executable, hb, "--event", "label",
                                "--label", "pomiar CarPlay audio PoC"],
                               timeout=5, check=False)
        except Exception:  # noqa: BLE001
            pass  # pomiar wazniejszy niz etykieta na telefonie

    pending_hits: list[tuple[float, str, str]] = []  # (ts, ua, remote)
    count = 0
    for line in tail(log_path, args.since):
        m = HIT_RE.match(line)
        if m:
            try:
                ts = parse_ts(m.group("ts"))
            except ValueError:
                continue
            pending_hits.append((ts, m.group("ua"), m.group("rem")))
            continue
        m = OK_RE.match(line)
        if not m:
            continue
        if not pending_hits:
            continue  # OK bez HIT — nie nasze
        ts_hit, ua, rem = pending_hits.pop(0)
        count += 1
        dt = m.group("dt")
        ct = m.group("ct")
        rec = {
            "nr": count,
            "ts_local": fmt_local(ts_hit),
            "remote": rem,
            "dt_s": float(dt),
            "ctype": ct,
            "ua": ua,
        }
        if args.json:
            print(json.dumps(rec, ensure_ascii=False))
        else:
            print("  %-2d  %s   %-13s   %-4s   %-9s   ok" %
                  (count, rec["ts_local"], rem, dt, ct))
        sys.stdout.flush()
        if count >= args.n:
            break

    print()
    print("podsumowanie: zarejestrowane proby: %d / spodziewane %d" % (count, args.n))
    if count < args.n:
        print("brakuje %d prob — serwer ich nie zobaczyl. Mozliwe: Siri nie rozpoznala frazy, "
              "LTE padlo w aucie, Shortcut sie powiesil, albo CarPlay odciecie dzwieku "
              "zablokowalo odpalenie."
              % (args.n - count))
    print("ty mowisz w aucie, czy zagralo przez glosnik, czy bylo zrozumiale")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
