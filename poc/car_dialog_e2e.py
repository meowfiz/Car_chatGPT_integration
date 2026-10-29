"""E2E dialogu auta (openspec car-dialog-okna, zadanie 4.1): prawdziwa sciezka HTTP -> /api/car/say.

Dwie czesci:
  chain  -- przebieg z zadania 4.1 (projekty -> przejscie -> polecenia -> gdzie jestem -> wroc)
  table  -- wiersze z notes/car_dialog_scenariusze.md, ktorych stan przed to `main` albo W(projekt,maszyna);
            stan budowany wypowiedziami ("przejdz do <p> w <m>"), nie zapisem pliku.
Wiersze z pending / trail / cisza sa pomijane (SKIP z powodem) -- pokrywa je test jednostkowy huba.

Uzycie: python poc/car_dialog_e2e.py [--url https://localhost:8788] [--token T] [--only chain|table] [--json]
Token: --token, CAR_TOKEN albo pierwszy token z hub tools/voice_gateway.load_car_tokens().
Kod wyjscia 0 = brak FAIL, 1 = jest FAIL, 2 = brak polaczenia lub tokenu. Stdlib only, ASCII.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
import time
import unicodedata
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TABLE = os.path.join(HERE, "..", "notes", "car_dialog_scenariusze.md")
HUB_TOOLS = os.path.join(HERE, "..", "..", "project_integration", "tools")
MACH = {"praca": "w pracy", "dom": "w domu"}
LQ, RQ = "„", "”"


def plain(t):
    t = unicodedata.normalize("NFKD", str(t or "").replace("ł", "l").replace("Ł", "L"))
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def parse_table(text):
    """Wiersze tabeli -> list[dict(n, before, said, outcome, after, contains)]. Pure."""
    rows = []
    for ln in text.splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) == 6 and cells[0].isdigit():
            rows.append(dict(n=int(cells[0]), before=cells[1], said=cells[2], outcome=cells[3],
                             after=cells[4], contains=cells[5]))
    return rows


def parse_state(cell):
    """'main' -> ('main', None, None); 'W(Car,praca)' -> ('window', 'Car', 'praca'); inne -> None. Pure."""
    c = cell.strip()
    if c == "main":
        return ("main", None, None)
    m = re.fullmatch(r"W\(([^,()]+),(\w+)\)", c)
    return ("window", m.group(1), m.group(2)) if m else None


def outcomes(cell):
    return [o.strip() for o in re.split(r"\blub\b", cell)]


def quoted(cell):
    return [plain(q) for q in re.findall(LQ + "([^" + RQ + "]+)" + RQ, cell)]


class Client:
    def __init__(self, url, token):
        self.url, self.token = url.rstrip("/"), token
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

    def say(self, sid, text, timeout=60):
        req = urllib.request.Request(
            self.url + "/api/car/say",
            data=json.dumps({"session_id": sid, "text": text}, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8", "Authorization": "Bearer " + self.token})
        with urllib.request.urlopen(req, timeout=timeout, context=self.ctx) as r:
            return json.loads(r.read().decode("utf-8", "replace"))


def get_token(arg):
    if arg or os.environ.get("CAR_TOKEN"):
        return arg or os.environ["CAR_TOKEN"]
    sys.path.insert(0, HUB_TOOLS)
    import voice_gateway as g
    toks = sorted(g.load_car_tokens())
    return toks[0] if toks else ""


def check(res, want_outcomes, want_state, contains):
    """List of problems (empty = PASS). Pure."""
    bad = []
    if want_outcomes and res.get("outcome") not in want_outcomes:
        bad.append("outcome %r, oczekiwano %s" % (res.get("outcome"), want_outcomes))
    st = res.get("state") or {}
    if want_state:
        mode, proj, mach = want_state
        if st.get("mode") != mode:
            bad.append("mode %r, oczekiwano %r" % (st.get("mode"), mode))
        if proj and plain(proj) not in plain(st.get("project")):
            bad.append("project %r, oczekiwano %r" % (st.get("project"), proj))
        if mach and plain(mach) not in plain(st.get("machine")):
            bad.append("machine %r, oczekiwano %r" % (st.get("machine"), mach))
    txt = plain(res.get("text"))
    for q in contains:
        if q not in txt:
            bad.append("tekst %r nie zawiera %r" % (res.get("text"), q))
    return bad


CHAIN = [
    ("jakie projekty teraz pracuja", ["answered"], ("main", None, None)),
    ("przejdz do projektu car integration", ["moved", "pending"], None),
    ("w pracy", ["moved", "answered", "pending"], None),
    ("gdzie jestem", ["where"], ("window", "Car", None)),
    ("powiedz oknu odpowiedz jednym slowem ok", ["queued", "answered"], ("window", "Car", None)),
    ("gdzie pracujemy", ["where"], ("window", "Car", None)),
    ("wroc", ["moved"], ("main", None, None)),
    ("gdzie jestem", ["where"], ("main", None, None)),
]


def run_chain(cl, tag):
    sid = "e2e-chain-%s" % tag
    out = []
    for said, oc, st in CHAIN:
        t0 = time.time()
        try:
            res = cl.say(sid, said)
            bad = check(res, oc, st, [])
        except Exception as exc:  # noqa: BLE001
            res, bad = {}, ["blad: %r" % (exc,)]
        out.append(dict(part="chain", said=said, dt=round(time.time() - t0, 1), bad=bad, text=res.get("text")))
    return out


def run_table(cl, tag):
    out = []
    for r in parse_table(open(TABLE, encoding="utf-8").read()):
        before, after = parse_state(r["before"]), parse_state(r["after"])
        same = r["after"].startswith("bez zmian")
        if before is None or (after is None and not same):
            out.append(dict(part="table", n=r["n"], said=r["said"], bad=[],
                            skip="stan nieodtwarzalny wypowiedziami"))
            continue
        sid = "e2e-t%s-%d" % (tag, r["n"])
        try:
            if before[0] == "window":
                cl.say(sid, "przejdz do %s %s" % (before[1], MACH.get(before[2], "")))
            res = cl.say(sid, r["said"])
            bad = check(res, outcomes(r["outcome"]), before if same else after, quoted(r["contains"]))
        except Exception as exc:  # noqa: BLE001
            bad = ["blad: %r" % (exc,)]
        out.append(dict(part="table", n=r["n"], said=r["said"], bad=bad))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default=os.environ.get("CAR_GATEWAY_URL", "https://localhost:8788"))
    ap.add_argument("--token", default="")
    ap.add_argument("--only", choices=["chain", "table"])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    token = get_token(a.token)
    if not token:
        print("BRAK TOKENU (--token / CAR_TOKEN / car_tokens.json)", file=sys.stderr)
        return 2
    cl, tag = Client(a.url, token), str(int(time.time()))
    try:
        cl.say("e2e-ping-" + tag, "gdzie jestem", timeout=15)
    except Exception as exc:  # noqa: BLE001
        print("BRAK POLACZENIA z %s/api/car/say: %r" % (a.url, exc), file=sys.stderr)
        return 2
    res = []
    if a.only != "table":
        res += run_chain(cl, tag)
    if a.only != "chain":
        res += run_table(cl, tag)
    for r in res:
        status = "SKIP" if r.get("skip") else ("FAIL" if r["bad"] else "PASS")
        print("%-5s %-6s %s %s" % (status, r["part"], r.get("n") or r["said"], "; ".join(r["bad"]) or r.get("skip", "")))
    if a.json:
        print(json.dumps(res, ensure_ascii=False))
    fails = sum(1 for r in res if r["bad"])
    print("PASS %d, FAIL %d, SKIP %d" % (sum(1 for r in res if not r["bad"] and not r.get("skip")),
                                         fails, sum(1 for r in res if r.get("skip"))))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
