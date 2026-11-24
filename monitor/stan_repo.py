"""notes/STAN.json: small per-repo state file for the Home Assistant add-on (emergency mode).

Written by monitor/auto_sync.py right before the gates, so it is committed with the session note.
A reader that has only GitHub (both PCs off) learns: project, time, machine, last task, the two
`## Na glos` lines and the counts of `## Zlecone`. Nothing else leaves the repo: no paths, no note
body, no other sections (the same text is already spoken aloud in the car, ZASADY 1.1 / 7.6).

Plan: notes/PLAN_auto_awaryjne_i_telefon_glos.md, section 2 step 1. Standard library only, ASCII only.
"""
from __future__ import annotations

import datetime as _dt
import glob
import json
import os
import re
import subprocess

SCHEMA = 1
STAN_REL = os.path.join("notes", "STAN.json")
QUIET = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}

_H2 = re.compile(r"^##\s+(.*?)\s*$")
_LINE = re.compile(r"^\s*(Zrobione|W toku)\s*:\s*(.*?)\s*$", re.IGNORECASE)
_ZLEC = re.compile(r"^\s*-\s*\[(wykonane|czeka|problem)\]", re.IGNORECASE)


def section(note_text, name):
    """Lines of the `## <name>` section (heading excluded), up to the next `## `. Pure."""
    out, inside = [], False
    for line in (note_text or "").splitlines():
        m = _H2.match(line)
        if m:
            inside = m.group(1).strip().lower() == name.lower()
            continue
        if inside:
            out.append(line)
    return out


def na_glos(note_text):
    """(zrobione, w_toku) from the `## Na glos` section; '' when a line is missing. Pure.
    The heading is matched with and without diacritics ('Na glos' / 'Na g\u0142os')."""
    lines = section(note_text, "Na g\u0142os") or section(note_text, "Na glos")
    got = {"zrobione": "", "w toku": ""}
    for line in lines:
        m = _LINE.match(line)
        if m and not got[m.group(1).lower()]:
            got[m.group(1).lower()] = m.group(2)
    return got["zrobione"], got["w toku"]


def zlecone_counts(note_text):
    """{'wykonane': n, 'czeka': n, 'problem': n} from the `## Zlecone` section only. Pure."""
    counts = {"wykonane": 0, "czeka": 0, "problem": 0}
    for line in section(note_text, "Zlecone"):
        m = _ZLEC.match(line)
        if m:
            counts[m.group(1).lower()] += 1
    return counts


def build_stan(note_text, project, machine, last_commit_title, now_iso):
    """The whole state document. Pure; only the fields below are ever emitted."""
    zrobione, w_toku = na_glos(note_text)
    return {
        "schema": SCHEMA,
        "projekt": project,
        "czas": now_iso,
        "maszyna": machine,
        "ostatnie_zadanie": last_commit_title,
        "zrobione": zrobione,
        "w_toku": w_toku,
        "zlecone": zlecone_counts(note_text),
    }


def same_but_time(old, new):
    """True when two state documents differ at most in 'czas' and 'ostatnie_zadanie'. Pure.
    The commit title is ignored: every commit changes it, so comparing it would make each sync
    rewrite STAN.json and create the next commit (endless one-file commits)."""
    if not isinstance(old, dict) or not isinstance(new, dict):
        return False
    a, b = dict(old), dict(new)
    for k in ("czas", "ostatnie_zadanie"):
        a.pop(k, None)
        b.pop(k, None)
    return a == b


def pick_note(repo_dir, today):
    """Today's note (latest by name), else the newest note file by name, else None."""
    d = os.path.join(repo_dir, "notes", "sesje")
    todays = sorted(glob.glob(os.path.join(d, today + "-*.md")))
    if todays:
        return todays[-1]
    allnotes = sorted(glob.glob(os.path.join(d, "*.md")))
    return allnotes[-1] if allnotes else None


def machine_name(env=None):
    """Same source as the 'Maszyna:' commit footer (tools/git_hooks/prepare-commit-msg)."""
    env = os.environ if env is None else env
    m = env.get("MONITOR_MACHINE") or env.get("COMPUTERNAME") or ""
    if not m:
        import socket
        m = socket.gethostname()
    return m[len("DESKTOP-"):] if m.startswith("DESKTOP-") else m


def _git_title(repo_dir):
    r = subprocess.run(["git", "log", "-1", "--format=%s"], cwd=repo_dir, capture_output=True,
                       encoding="utf-8", errors="replace", **QUIET)
    return (r.stdout or "").strip() if r.returncode == 0 else ""


def write_stan(repo_dir, now=None):
    """Impure wrapper. Returns 'written' | 'unchanged' | 'no-note'. Rewrites the file only when
    something other than 'czas' changed, so a sync does not create a commit for the timestamp alone."""
    now = now or _dt.datetime.now()
    note = pick_note(repo_dir, now.date().isoformat())
    if not note:
        return "no-note"
    with open(note, "rb") as f:
        text = f.read().decode("utf-8", "replace")
    stan = build_stan(text, os.path.basename(os.path.abspath(repo_dir)), machine_name(),
                      _git_title(repo_dir), now.isoformat(timespec="seconds"))
    path = os.path.join(repo_dir, STAN_REL)
    try:
        with open(path, "rb") as f:
            old = json.loads(f.read().decode("utf-8"))
    except (OSError, ValueError):
        old = None
    if same_but_time(old, stan):
        return "unchanged"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(stan, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return "written"
