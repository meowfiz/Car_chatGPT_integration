"""PoC bridge: voice question from the car -> Claude (read only) -> short Polish answer.

Single throwaway file (OpenSpec change poc-carplay-command). ASCII only per ZASADY 4.1.

Endpoints
    GET  /health                 -> "ok"
    POST /ask/<secret>           -> plain text answer (Shortcuts feeds it to Speak Text)
         body: JSON {"q": "..."} or raw audio bytes (Content-Type audio/*)
         query: ?format=json     -> JSON {"q": ..., "a": ..., "ms": ..., "stt_ms": ...}

Safety (OpenSpec D6)
    - binds to the Tailscale address only, never 0.0.0.0
    - secret in the path, rate limited, every call logged
    - claude runs with read only tools; in print mode anything that would prompt is denied

Run
    python poc/ask_server.py
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SECRET = os.environ.get("ASK_SECRET", "zmien-mnie")
BIND = os.environ.get("ASK_BIND", "100.95.41.116")
PORT = int(os.environ.get("ASK_PORT", "8787"))
ROOT = os.environ.get("ASK_ROOT", r"D:\claude_projects")
MODEL = os.environ.get("ASK_MODEL", "sonnet")
CLAUDE_TIMEOUT = int(os.environ.get("ASK_TIMEOUT", "120"))
WHISPER_MODEL = os.environ.get("ASK_WHISPER", "small")
WHISPER_DEVICE = os.environ.get("ASK_WHISPER_DEVICE", "cpu")
MAX_BODY = 25 * 1024 * 1024
MIN_INTERVAL = 3.0
MAX_PER_HOUR = 60
LOG_PATH = os.path.join(ROOT, "Car_chatGPT_integration", "project_files", "run_files",
                        "ask_server.log")

READ_ONLY_ALLOW = ["Read", "Glob", "Grep", "Bash(git log:*)", "Bash(git status:*)",
                   "Bash(git show:*)", "Bash(git diff:*)"]
READ_ONLY_DENY = ["Write", "Edit", "NotebookEdit", "WebFetch", "WebSearch",
                  "Bash(git push:*)", "Bash(git commit:*)", "Bash(git add:*)", "Task"]

SYSTEM = (
    "Odpowiadasz kierowcy, ktory slucha odpowiedzi przez glosniki samochodu. "
    "Zasady: po polsku, maksymalnie trzy zdania, bez markdown, bez sciezek, bez kodu, "
    "bez list punktowanych. Liczby mow slownie tylko gdy sa krotkie. "
    "Opierasz sie wylacznie na plikach w katalogu projektow: notes/start.md, "
    "notes/sesje/, openspec/STATUS.md, openspec/changes/*/tasks.md oraz historii git. "
    "Jesli danych nie ma, powiedz wprost, ze ich nie ma, i nie zgaduj."
)

_lock = threading.Lock()
_calls = []
_worker = None
_worker_lock = threading.Lock()


def log(kind, msg):
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    line = "%s %s %s" % (stamp, kind, msg)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def rate_ok():
    now = time.time()
    with _lock:
        while _calls and now - _calls[0] > 3600:
            _calls.pop(0)
        if _calls and now - _calls[-1] < MIN_INTERVAL:
            return False, "za szybko"
        if len(_calls) >= MAX_PER_HOUR:
            return False, "limit godzinowy"
        _calls.append(now)
    return True, ""


def whisper_worker():
    """Runs as a separate process.

    Measured 2026-09-14: ctranslate2 kills the whole interpreter with an access
    violation when the model is driven from a server worker thread on Windows, and
    no try/except can catch that. In its own process the same call is fine, and a
    crash then costs one request instead of the server.

    Protocol: one audio path per input line, one JSON object per output line.
    """
    compute = "float16" if WHISPER_DEVICE == "cuda" else "int8"
    from faster_whisper import WhisperModel

    model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=compute)
    sys.stdout.write(json.dumps({"ready": True, "model": WHISPER_MODEL,
                                 "device": WHISPER_DEVICE}) + "\n")
    sys.stdout.flush()
    for line in sys.stdin:
        path = line.strip()
        if not path:
            continue
        try:
            segments, _info = model.transcribe(path, language="pl", beam_size=5)
            out = {"text": " ".join(seg.text.strip() for seg in segments).strip()}
        except Exception as exc:  # noqa: BLE001 - the server must hear about it
            out = {"error": str(exc)[:300]}
        sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
        sys.stdout.flush()
    return 0


def worker_start():
    global _worker
    if _worker is not None and _worker.poll() is None:
        return
    cmd = [sys.executable, os.path.abspath(__file__), "--whisper-worker"]
    _worker = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
                               bufsize=1)
    hello = _worker.stdout.readline()
    if not hello:
        raise RuntimeError("proces transkrypcji nie wystartowal")
    log("whisper", hello.strip())


def transcribe(raw, suffix):
    path = None
    try:
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "wb") as fh:
            fh.write(raw)
        with _worker_lock:
            worker_start()
            _worker.stdin.write(path + "\n")
            _worker.stdin.flush()
            line = _worker.stdout.readline()
        if not line:
            raise RuntimeError("proces transkrypcji padl")
        out = json.loads(line)
        if "error" in out:
            raise RuntimeError(out["error"])
        return out.get("text", "").strip()
    finally:
        if path:
            try:
                os.remove(path)
            except OSError:
                pass


def ask_claude(question):
    cmd = [
        "claude", "-p", question,
        "--output-format", "text",
        "--model", MODEL,
        "--append-system-prompt", SYSTEM,
        "--allowedTools", *READ_ONLY_ALLOW,
        "--disallowedTools", *READ_ONLY_DENY,
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=CLAUDE_TIMEOUT,
                          shell=(os.name == "nt"))
    if proc.returncode != 0:
        detail = (proc.stderr or "claude zwrocil %d" % proc.returncode).strip()
        raise RuntimeError(detail[:300])
    return proc.stdout.strip()


def for_speech(text):
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"[*_`#>|\[\]]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:700]


class Handler(BaseHTTPRequestHandler):
    server_version = "ask-poc/1"

    def log_message(self, fmt, *args):
        pass

    def _send(self, code, body, ctype="text/plain; charset=utf-8"):
        raw = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path.split("?")[0] == "/health":
            self._send(200, "ok")
        else:
            self._send(404, "nie ma takiej sciezki")

    def do_POST(self):
        started = time.time()
        path = self.path.split("?")[0]
        want_json = "format=json" in self.path
        if not path.startswith("/ask/") or path[len("/ask/"):] != SECRET:
            log("deny", "zla sciezka z %s" % self.client_address[0])
            self._send(403, "brak dostepu")
            return

        ok, why = rate_ok()
        if not ok:
            log("deny", "rate limit: %s" % why)
            self._send(429, "Poczekaj chwile, %s." % why)
            return

        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            self._send(413, "zle cialo zadania")
            return
        raw = self.rfile.read(length)
        ctype = (self.headers.get("Content-Type") or "").lower()

        t_stt = 0.0
        try:
            if ctype.startswith("audio/") or ctype == "application/octet-stream":
                suffix = ".m4a" if ("m4a" in ctype or "mp4" in ctype) else ".wav"
                t0 = time.time()
                question = transcribe(raw, suffix)
                t_stt = time.time() - t0
                source = "audio"
            else:
                payload = json.loads(raw.decode("utf-8"))
                question = (payload.get("q") or "").strip()
                source = "text"
            if not question:
                raise ValueError("puste pytanie")
        except Exception as exc:  # noqa: BLE001 - every failure must answer by voice
            log("error", "wejscie: %s" % exc)
            self._send(400, "Nie zrozumialem pytania.")
            return

        log("ask", "%s (stt %.1f s): %s" % (source, t_stt, question))
        try:
            answer = for_speech(ask_claude(question))
        except subprocess.TimeoutExpired:
            log("error", "timeout claude")
            self._send(504, "Zadanie trwa za dlugo, sprawdz pozniej.")
            return
        except Exception as exc:  # noqa: BLE001
            log("error", "claude: %s" % exc)
            self._send(500, "Nie udalo sie uzyskac odpowiedzi.")
            return

        ms = int((time.time() - started) * 1000)
        log("answer", "%d ms: %s" % (ms, answer[:160]))
        if want_json:
            body = json.dumps({"q": question, "a": answer, "ms": ms,
                               "stt_ms": int(t_stt * 1000)}, ensure_ascii=False)
            self._send(200, body, "application/json; charset=utf-8")
        else:
            self._send(200, answer)


def main():
    if "--whisper-worker" in sys.argv:
        return whisper_worker()
    if SECRET == "zmien-mnie":
        print("USTAW ASK_SECRET przed uruchomieniem")
        return 2
    log("start", "http://%s:%d/ask/<secret> root=%s model=%s whisper=%s/%s"
        % (BIND, PORT, ROOT, MODEL, WHISPER_MODEL, WHISPER_DEVICE))
    ThreadingHTTPServer((BIND, PORT), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
