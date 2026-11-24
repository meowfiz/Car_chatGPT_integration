#!/usr/bin/env python3
"""
gpu_watch.py -- passive meter of the GPU and of the host's memory, for the voice gateway's safe margin.

What changed 2026-10-26 (openspec/changes/voice-safe-margin, user: "bezpieczny margines, VCC nigdy
przeciazone"). The old version rendered a unique text on VCC every 90 s and restarted VCC after three
failed probes. That probe was a GPU job outside the gateway's queue, it aged the VCC worker
(chatterbox-tts 0.1.7 leaves 3 forward hooks per render: +0.24 s of compute per second of speech per
100 renders) and on 26.10 18:30 it restarted VCC because a test of mine held the card. Now nothing
here touches VCC: every SAMPLE_S it reads nvidia-smi (VRAM, utilisation) and the host's free commit
charge and writes ~/.claude/gpu_state.json. The gateway decides per reply (clone_admit) with its own
margins; a stale or missing file means "no clone", never a restart.

State: {"at", "mode": "passive", "vram_used_mb", "vram_total_mb", "vram_free_mb", "util",
        "samples": [[t, util], ...] (last SAMPLES_KEEP_S), "commit_free_gb", "commit_limit_gb",
        "machine", "error"}

Standard library only, ASCII only (ZASADY 4.1). Parsing and the payload are pure (ZASADY 4.5).
"""

import argparse
import json
import os
import platform
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SAMPLE_S = float(os.environ.get("GPU_WATCH_SAMPLE_S", "2"))
SAMPLES_KEEP_S = 12.0
STATE_FILE = os.path.join(os.path.expanduser("~"), ".claude", "gpu_state.json")
LOCK = os.path.join(tempfile.gettempdir(), "monitor_gpu_watch.lock")
LOG_FILE = os.path.join(ROOT, "project_files", "run_files", "gpu_watch.log")
QUIET = {"creationflags": 0x08000000} if os.name == "nt" else {}


def log(msg):
    line = "%s [gpu-watch] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


# -- pure (tested in pack/tests/test_gpu_watch.py) ---------------------------------------------

def parse_smi(text):
    """'used, total, util' (nvidia-smi csv, noheader, nounits; first GPU) -> (used_mb, total_mb, util)
    or None when the line does not parse. Pure."""
    for line in (text or "").splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 3:
            try:
                return int(float(parts[0])), int(float(parts[1])), int(float(parts[2]))
            except ValueError:
                return None
    return None


def push_sample(samples, now, util, keep_s=SAMPLES_KEEP_S):
    """The utilisation history the gateway reads: [[t, util], ...] of the last keep_s seconds. Pure."""
    out = [s for s in (samples or []) if now - s[0] <= keep_s]
    if util is not None:
        out.append([round(now, 2), int(util)])
    return out


def state_payload(now, smi, commit, samples, error=None):
    """gpu_state.json contents from one reading. smi = (used, total, util) or None; commit =
    (free_gb, limit_gb) or (None, None). Pure."""
    used, total, util = smi if smi else (None, None, None)
    free_gb, limit_gb = commit
    return {"at": round(now, 2), "mode": "passive",
            "vram_used_mb": used, "vram_total_mb": total,
            "vram_free_mb": (total - used) if smi else None,
            "util": util, "samples": samples,
            "commit_free_gb": free_gb, "commit_limit_gb": limit_gb,
            "machine": platform.node(), "error": error}


# -- IO ---------------------------------------------------------------------------------------

def read_smi():
    r = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu",
                        "--format=csv,noheader,nounits"], capture_output=True, timeout=10, **QUIET)
    return parse_smi(r.stdout.decode("utf-8", "replace")) if r.returncode == 0 else None


def read_commit():
    """(free commit GB, commit limit GB). Windows: GlobalMemoryStatusEx -- ullTotalPageFile and
    ullAvailPageFile are the commit limit and what is left of it (2026-10-26: 213,4 of 220,3 GB used,
    VCC answered 500 'DefaultCPUAllocator: not enough memory' when it ran out). Linux: /proc/meminfo."""
    if os.name == "nt":
        import ctypes

        class MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = MS()
        m.dwLength = ctypes.sizeof(MS)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            return round(m.ullAvailPageFile / 2.0 ** 30, 2), round(m.ullTotalPageFile / 2.0 ** 30, 2)
        return None, None
    try:
        kv = {}
        with open("/proc/meminfo", encoding="utf-8") as fh:
            for line in fh:
                k, _, v = line.partition(":")
                kv[k] = int(v.split()[0])
        limit, used = kv["CommitLimit"], kv["Committed_AS"]
        return round((limit - used) / 2.0 ** 20, 2), round(limit / 2.0 ** 20, 2)
    except (OSError, KeyError, ValueError, IndexError):
        return None, None


def write_state(path, payload):
    """Atomic write (tmp + rename) so a reader never sees a half-written file."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        os.replace(tmp, path)
    except OSError:
        pass


def touch_lock(now):
    try:
        with open(LOCK, "w", encoding="utf-8") as fh:
            json.dump({"pid": os.getpid(), "at": now, "machine": platform.node()}, fh)
    except OSError:
        pass


def drop_lock():
    try:
        os.remove(LOCK)
    except OSError:
        pass


# -- loop -------------------------------------------------------------------------------------

def run(once=False):
    log("start (passive): every %.1f s, no render, no VCC restart" % SAMPLE_S)
    samples, last_log = [], 0.0
    while True:
        now = time.time()
        touch_lock(now)
        err = None
        try:
            smi = read_smi()
            if smi is None:
                err = "nvidia-smi gave nothing"
        except (OSError, subprocess.SubprocessError) as exc:
            smi, err = None, "nvidia-smi: %s" % exc
        try:
            commit = read_commit()
        except Exception as exc:  # noqa: BLE001 -- a missing reading is reported, never fatal
            commit, err = (None, None), (err or "commit: %s" % exc)
        samples = push_sample(samples, now, smi[2] if smi else None)
        payload = state_payload(now, smi, commit, samples, err)
        write_state(STATE_FILE, payload)
        if now - last_log >= 600 or err:      # one line per 10 min (and every error), not every 2 s
            log("vram free %s MiB, util %s%%, commit free %s GB%s"
                % (payload["vram_free_mb"], payload["util"], payload["commit_free_gb"],
                   (" ERROR " + err) if err else ""))
            last_log = now
        if once:
            return 0
        time.sleep(SAMPLE_S)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--once", action="store_true", help="one reading then exit (diagnostics)")
    args = ap.parse_args(argv)
    try:
        return run(once=args.once)
    finally:
        if args.once:
            drop_lock()


if __name__ == "__main__":
    sys.exit(main())
