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

try:                                    # imported as poc.ask_server (tests)
    from poc import intent
except ImportError:                     # run as a script: python poc/ask_server.py
    import intent

SECRET = os.environ.get("ASK_SECRET", "zmien-mnie")
BIND = os.environ.get("ASK_BIND", "100.95.41.116")
PORT = int(os.environ.get("ASK_PORT", "8787"))
ROOT = os.environ.get("ASK_ROOT", r"D:\claude_projects")
# Repositories do NOT have to sit under one root, and they sit elsewhere on every machine.
# ASK_REPOS is a ';' separated list of absolute paths; empty = every git repo directly under ROOT.
REPOS_RAW = os.environ.get("ASK_REPOS", "")
SYNC = os.environ.get("ASK_SYNC", "1") != "0"
SYNC_TIMEOUT = float(os.environ.get("ASK_SYNC_TIMEOUT", "8"))
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
    # ZASADY 4.10: this pipe carries Polish text, and sys.stdout here defaults to the console
    # code page (cp1250), which the parent reads as UTF-8 -- one 'l' with a stroke killed every
    # transcription (2026-09-16).
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
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
        sys.stdout.write(json.dumps(out) + "\n")  # ASCII escapes: code-page proof
        sys.stdout.flush()
    return 0


def worker_start():
    global _worker
    if _worker is not None and _worker.poll() is None:
        return
    cmd = [sys.executable, os.path.abspath(__file__), "--whisper-worker"]
    env = dict(os.environ, PYTHONIOENCODING="utf-8")  # the child writes what we read (ZASADY 4.10)
    _worker = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
                               bufsize=1, env=env)
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


def repo_paths():
    """Absolute paths of the repositories this machine answers about."""
    out = []
    if REPOS_RAW.strip():
        out = [p.strip().strip('"') for p in REPOS_RAW.split(";") if p.strip()]
    else:
        try:
            for name in sorted(os.listdir(ROOT)):
                out.append(os.path.join(ROOT, name))
        except OSError:
            pass
    return [p for p in out if os.path.isdir(os.path.join(p, ".git"))]


REPOS = repo_paths()

try:
    ALIASES = intent.load_aliases()
except (OSError, ValueError):           # a broken table must not kill the bridge
    ALIASES = {"repos": {}, "wszystkie": [], "min_ratio": 0.82}


def repos_for(repo):
    """Directories the model gets for this intent.

    A recognised repository narrows the scope to one tree - the only measurable time win of the
    intent layer (prerejestracja voice-intent 5.2). A name this machine does not have falls back
    to everything, because answering from the wrong tree is worse than answering slowly.
    """
    if not repo or repo == "*" or not REPOS:
        return REPOS, "*"
    want = repo.strip().lower()
    hit = [p for p in REPOS if os.path.basename(p.rstrip("\\/")).lower() == want]
    if not hit:
        return REPOS, "*"
    return hit, repo


def git(args, cwd, timeout):
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"     # never hang on a credential prompt, nobody is watching
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout, env=env)


def age_phrase(iso):
    """'2026-09-15 11:02:03 +0200' -> 'X minut/godzin/dni temu' (spoken, so no exact stamps)."""
    try:
        when = datetime.strptime(iso.strip()[:19], "%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return "nieznany czas"
    minutes = max(0, int((datetime.now() - when).total_seconds() // 60))
    if minutes < 60:
        return "%d min temu" % minutes
    if minutes < 60 * 48:
        return "%d h temu" % (minutes // 60)
    return "%d dni temu" % (minutes // 1440)


def sync_repo(path, timeout):
    """One repository: fast-forward to the remote if that is safe, then report what we have.

    Never rebases, never pushes, never touches a dirty tree (ZASADY 2.3 / 2.7): the answering
    machine is a reader. A repo it cannot reach still answers - from the local state, with the
    age said out loud, which is the honest version of 'nie wiem, czy to aktualne'.
    """
    name = os.path.basename(path.rstrip("\\/"))
    try:
        before = git(["rev-parse", "--short", "HEAD"], path, 10).stdout.strip()
        dirty = git(["status", "--porcelain"], path, 15).stdout.strip()
        if dirty:
            state = "lokalne zmiany, nie odswiezam"
        else:
            pull = git(["pull", "--ff-only"], path, timeout)
            after = git(["rev-parse", "--short", "HEAD"], path, 10).stdout.strip()
            if pull.returncode != 0:
                state = "NIE odswiezone (brak polaczenia albo rozjazd z remote)"
            elif before == after:
                state = "bez zmian na remote"
            else:
                state = "podciagniete z remote"
    except (subprocess.TimeoutExpired, OSError) as exc:
        return "%s: NIE odswiezone (%s)" % (name, type(exc).__name__)
    try:
        head = git(["log", "-1", "--format=%h|%ci|%s"], path, 10).stdout.strip()
        sha, when, subject = head.split("|", 2)
        return "%s: %s, ostatni commit %s %s (%s)" % (name, state, sha, age_phrase(when),
                                                      subject[:60])
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return "%s: %s" % (name, state)


def sync_all(timeout):
    """Every repository in parallel - the wall clock is one pull, not their sum."""
    if not SYNC or not REPOS:
        return ["synchronizacja wylaczona"] if not SYNC else ["brak repozytoriow"]
    results = [None] * len(REPOS)

    def one(i, path):
        results[i] = sync_repo(path, timeout)

    threads = [threading.Thread(target=one, args=(i, p), daemon=True)
               for i, p in enumerate(REPOS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=timeout + 5)
    return [r for r in results if r] or ["nie udalo sie sprawdzic repozytoriow"]


def context_block(lines):
    return ("STAN DANYCH sprawdzony przed ta odpowiedzia (kazde repozytorium osobno):\n"
            + "\n".join("- " + ln for ln in lines)
            + "\nJesli repozytorium jest oznaczone jako NIE odswiezone, a pytanie go dotyczy, "
              "powiedz w jednym zdaniu, ze odpowiadasz ze stanu sprzed podanego czasu.\n\n"
              "PYTANIE: ")


def ask_claude(question, dirs=None, extra_system=""):
    dirs = REPOS if dirs is None else dirs
    system = (SYSTEM + " " + extra_system).strip() if extra_system else SYSTEM
    # The question goes on stdin, never into argv: on Windows `claude` is claude.CMD and cmd.exe
    # truncates an argument at the first newline, so a question with the freshness report in front
    # of it arrived as the report header alone (measured 2026-09-16, two runs).
    cmd = [
        "claude", "-p",
        "--output-format", "text",
        "--model", MODEL,
        "--append-system-prompt", " ".join(system.split()),
        "--allowedTools", *READ_ONLY_ALLOW,
        "--disallowedTools", *READ_ONLY_DENY,
    ]
    for path in dirs[1:]:
        cmd += ["--add-dir", path]
    proc = subprocess.run(cmd, input=question, cwd=(dirs[0] if dirs else ROOT), capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=CLAUDE_TIMEOUT,
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

        # The pull runs while Whisper transcribes, so freshness costs no extra wall clock:
        # transcription measured 2,1 s, a fetch of four repositories is under that.
        sync_box = {}
        sync_thread = threading.Thread(
            target=lambda: sync_box.setdefault("lines", sync_all(SYNC_TIMEOUT)), daemon=True)
        sync_thread.start()

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

        parsed = intent.parse(question, ALIASES)
        log("ask", "%s (stt %.1f s) [%s %s/%s]: %s"
            % (source, t_stt, parsed["intent"], parsed["repo"], parsed["repo_reason"], question))

        # Recognised but not executed: every write needs the gates of ZASADY 2.7-2.9. HTTP 200
        # on purpose - the Shortcut speaks the body, an error code would end in silence.
        if parsed["intent"] != "ask":
            said = intent.refusal(parsed["intent"])
            log("refuse", "%s: %s" % (parsed["intent"], question[:120]))
            if want_json:
                self._send(200, json.dumps({"q": question, "a": said, "intent": parsed,
                                            "ms": int((time.time() - started) * 1000)},
                                           ensure_ascii=False),
                           "application/json; charset=utf-8")
            else:
                self._send(200, said)
            return

        dirs, scope = repos_for(parsed["repo"])
        t0 = time.time()
        sync_thread.join(timeout=SYNC_TIMEOUT + 5)
        t_sync = time.time() - t0
        sync_lines = sync_box.get("lines") or ["nie zdazylem sprawdzic stanu repozytoriow"]
        log("sync", "czekalem %.1f s | %s" % (t_sync, " | ".join(sync_lines)))
        scoped = dict(parsed, repo=scope)
        try:
            answer = for_speech(ask_claude(context_block(sync_lines) + question, dirs,
                                           intent.scope_instruction(scoped)))
        except subprocess.TimeoutExpired:
            log("error", "timeout claude")
            self._send(504, "Zadanie trwa za dlugo, sprawdz pozniej.")
            return
        except Exception as exc:  # noqa: BLE001
            log("error", "claude: %s" % exc)
            self._send(500, "Nie udalo sie uzyskac odpowiedzi.")
            return

        ms = int((time.time() - started) * 1000)
        log("answer", "%d ms [zakres %s]: %s" % (ms, scope, answer[:160]))
        if want_json:
            body = json.dumps({"q": question, "a": answer, "ms": ms,
                               "stt_ms": int(t_stt * 1000), "sync_ms": int(t_sync * 1000),
                               "repos": sync_lines, "intent": scoped}, ensure_ascii=False)
            self._send(200, body, "application/json; charset=utf-8")
        else:
            self._send(200, answer)


def main():
    if "--whisper-worker" in sys.argv:
        return whisper_worker()
    if SECRET == "zmien-mnie":
        print("USTAW ASK_SECRET przed uruchomieniem")
        return 2
    log("start", "http://%s:%d/ask/<secret> model=%s whisper=%s/%s sync=%s"
        % (BIND, PORT, MODEL, WHISPER_MODEL, WHISPER_DEVICE, SYNC))
    if not REPOS:
        log("start", "UWAGA: zero repozytoriow - ustaw ASK_REPOS albo ASK_ROOT")
    for path in REPOS:
        log("start", "repo %s" % path)
    unknown = intent.unknown_aliases(ALIASES, intent.canonical_names())
    if unknown:
        log("start", "UWAGA: aliasy wskazuja na nieznane repozytoria: %s" % ", ".join(unknown))
    ThreadingHTTPServer((BIND, PORT), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
