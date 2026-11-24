"""straznik_git.py -- the ONLY place where the rules guard runs a child process (R-PUSH, ZASADY 2.10).

    unpushed(cwd) -> (ahead, oldest_commit_epoch) | None

One read-only call: `git log --format=%ct @{u}..HEAD` (one committer timestamp per unpushed commit, so the count
and the oldest commit come from a single process). Timeout GIT_TIMEOUT_S; any error (no git, no upstream, not a
repository, timeout) gives None -- never an exception. Never writes, never fetches, never pushes.
Kept out of straznik_regul.py so that module stays free of subprocess (test_hook_module_does_not_import_subprocess).
Standard library only. ASCII only.
"""
import os
import subprocess

import straznik_reguly as R

GIT_TIMEOUT_S = 1.0
_NOWIN = {"creationflags": 0x08000000} if os.name == "nt" else {}


def unpushed(cwd, timeout=GIT_TIMEOUT_S):
    try:
        if not cwd or not os.path.isdir(cwd):
            return None
        p = subprocess.run(["git", "-C", cwd, "log", "--format=%ct", "@{u}..HEAD"], capture_output=True,
                           timeout=timeout, stdin=subprocess.DEVNULL, **_NOWIN)
        if p.returncode != 0:
            return None
        return R.parsuj_log_push(p.stdout.decode("utf-8", "replace"))
    except Exception:
        return None
