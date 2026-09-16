"""Tests for the intent layer (OpenSpec change voice-intent).

ZASADY 4.4: every test names the failure it prevents, and every one of them was checked by
mutation - the note is in notes/sesje/2026-09-16-sesja.md.

Run: python -m pytest -q project_files/python/tests
"""

import json
import os
import sys
import threading
import urllib.request

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures",
                       "wypowiedzi.json")

from poc import intent  # noqa: E402 - after sys.path


@pytest.fixture(scope="module")
def table():
    return intent.load_aliases()


def utterances():
    with open(FIXTURE, "r", encoding="utf-8") as fh:
        return json.load(fh)["wypowiedzi"]


# --- normalisation ----------------------------------------------------------------------
# Failure prevented: comparing Whisper output (which has Polish letters and punctuation)
# against ASCII aliases, so that nothing ever matches and every question goes to all repos.

def test_normalize_strips_diacritics_and_punctuation():
    assert intent.normalize("Ile zadań zostało, w projekcie?") == \
        "ile zadan zostalo w projekcie"


# --- repository from garbled speech -----------------------------------------------------
# Failure prevented: a parser that only works on correctly pronounced names - which is
# exactly the problem it exists to solve. The input below is the REAL Whisper transcription
# from project_files/run_files/ask_server.log (2026-09-14), not an invented one.

def test_real_whisper_transcription_finds_the_repository(table):
    said = "Ile zadań zostalo w projekcie Carcha gpt integration i co jest następne."
    repo, reason = intent.match_repo(said, table)
    assert repo == "Car_chatGPT_integration"
    assert reason in ("exact", "fuzzy")


def test_misspelled_alias_still_matches(table):
    repo, reason = intent.match_repo("Co słychać w rybniksterze", table)
    assert repo == "RibnXtr2026"
    assert reason == "fuzzy"


# --- "*" has two meanings and the log must tell them apart ------------------------------
# Failure prevented: an accuracy measurement that counts "the rules gave up" as a success,
# because both cases came out as the same "*" with no reason attached.

def test_explicit_all_and_no_match_are_different_reasons(table):
    assert intent.match_repo("Co się dzieje we wszystkich projektach", table) == \
        ("*", "explicit-all")
    assert intent.match_repo("Jak się miewa pogoda w Toruniu", table) == ("*", "no-match")


def test_short_alias_never_matches_fuzzily(table):
    """'dom' (HA) must not swallow 'do domu'. A false hit answers about the wrong project."""
    repo, _reason = intent.match_repo("Ile mam kilometrów do domu", table)
    assert repo == "*"


# --- intent -----------------------------------------------------------------------------
# Failure prevented: a write request silently turning into a question - the driver asks for
# a note, hears an answer, and believes something was saved.

def test_note_is_not_a_question(table):
    parsed = intent.parse("Zanotuj, że trzeba dokończyć watchdoga", table)
    assert parsed["intent"] == "note"
    assert intent.refusal("note")


def test_queue_is_not_a_question(table):
    parsed = intent.parse("Dodaj zadanie: przemierzyć czas odpowiedzi", table)
    assert parsed["intent"] == "queue"
    assert intent.refusal("queue")


def test_plain_question_stays_ask(table):
    assert intent.parse("Ile zadań zostało w ha", table)["intent"] == "ask"


# --- sentence limit ---------------------------------------------------------------------
# Failure prevented: inventing a number nobody said ("krotko" is not a count), and dropping
# a number that was said, which is the driver's only way to shorten the answer.

def test_limit_from_words_and_digits():
    assert intent.parse_limit("powiedz w dwóch zdaniach") == 2
    assert intent.parse_limit("w 3 zdaniach proszę") == 3
    assert intent.parse_limit("w jednym zdaniu") == 1


def test_limit_is_none_when_no_number_was_said():
    assert intent.parse_limit("powiedz krótko") is None
    assert intent.parse_limit("") is None


# --- alias table hygiene ----------------------------------------------------------------
# Failure prevented: a typo in aliases.json silently disabling a repository - which looks
# exactly like a parser that cannot recognise it.

def test_unknown_alias_is_reported_and_parser_keeps_working():
    broken = {"min_ratio": 0.82, "wszystkie": [],
              "repos": {"HA": ["home assistant"], "Literoŵka": ["cos tam"]}}
    assert intent.unknown_aliases(broken, ["HA", "project_integration"]) == ["Literoŵka"]
    assert intent.match_repo("co w home assistant", broken)[0] == "HA"


def test_unknown_alias_check_is_silent_without_a_repo_map(table):
    """No map on this machine means we cannot warn - not that every alias is broken."""
    assert intent.unknown_aliases(table, []) == []


def test_shipped_alias_table_points_at_real_repositories(table):
    """Every canonical key must be a repository this machine knows, when the map exists."""
    names = intent.canonical_names()
    if not names:
        pytest.skip("brak ~/.claude/monitor_repos.env na tej maszynie")
    assert intent.unknown_aliases(table, names) == []


# --- scope ------------------------------------------------------------------------------
# Failure prevented: a recognised repository that does not narrow anything (no time win), or
# a name this machine does not have narrowing the scope to nothing (an answer about a repo
# that is not there).

def load_server(monkeypatch, **env):
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    sys.modules.pop("poc.ask_server", None)
    import importlib
    return importlib.import_module("poc.ask_server")


def test_recognised_repo_narrows_the_scope(tmp_path, monkeypatch):
    import subprocess
    for name in ("HA", "RibnXtr2026"):
        path = tmp_path / name
        path.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=str(path), check=True)
    srv = load_server(monkeypatch, ASK_SECRET="x", ASK_ROOT=str(tmp_path), ASK_REPOS="",
                      ASK_SYNC="0")
    dirs, scope = srv.repos_for("HA")
    assert scope == "HA"
    assert [os.path.basename(p) for p in dirs] == ["HA"]


def test_repo_this_machine_does_not_have_falls_back_to_everything(tmp_path, monkeypatch):
    import subprocess
    path = tmp_path / "HA"
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=str(path), check=True)
    srv = load_server(monkeypatch, ASK_SECRET="x", ASK_ROOT=str(tmp_path), ASK_REPOS="",
                      ASK_SYNC="0")
    dirs, scope = srv.repos_for("nie_ma_takiego")
    assert scope == "*"
    assert [os.path.basename(p) for p in dirs] == ["HA"]


def test_scope_instruction_names_the_repo_instead_of_asking():
    text = intent.scope_instruction({"repo": "HA", "limit_zdan": 2})
    assert "HA" in text and "2" in text
    assert "?" not in text          # a confirming question doubles the loop - decision 2026-09-16


# --- refusal travels as speech, not as an error -----------------------------------------
# Failure prevented: the Shortcut feeding an HTTP error code to Speak Text, so the driver
# hears silence (or an English system message) instead of the reason nothing happened.

def test_note_over_http_answers_200_with_a_polish_sentence(tmp_path, monkeypatch):
    from http.server import ThreadingHTTPServer
    srv = load_server(monkeypatch, ASK_SECRET="tajne", ASK_ROOT=str(tmp_path), ASK_REPOS="",
                      ASK_SYNC="0", ASK_BIND="127.0.0.1", ASK_PORT="0")
    monkeypatch.setattr(srv, "LOG_PATH", str(tmp_path / "log.txt"))
    monkeypatch.setattr(srv, "MIN_INTERVAL", 0.0)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        url = "http://127.0.0.1:%d/ask/tajne" % httpd.server_address[1]
        body = json.dumps({"q": "Zanotuj, że trzeba dokończyć watchdoga"}
                          ).encode("utf-8")
        req = urllib.request.Request(url, data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            assert resp.status == 200
            said = resp.read().decode("utf-8")
        assert "notat" in said.lower()
    finally:
        httpd.shutdown()


# --- the fixture itself -----------------------------------------------------------------
# Failure prevented: reporting parser accuracy on a fixture that quietly lost its provenance
# field, so nobody can tell desk-written utterances from real transcriptions.

def test_every_fixture_row_declares_its_source():
    rows = utterances()
    assert len(rows) >= 40
    for row in rows:
        assert row["zrodlo"] in ("log", "syntetyczna")
        assert row["oczekiwane"]
    assert sum(1 for r in rows if r["zrodlo"] == "log") >= 1


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
