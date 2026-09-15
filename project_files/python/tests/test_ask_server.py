"""Tests for the pure decisions of poc/ask_server.py (ZASADY 4.4: a test names the failure
it prevents). No network, no claude, no whisper - only functions that decide something.

Run: python -m pytest -q project_files/python/tests
"""

import os
import subprocess
import sys
from datetime import datetime, timedelta

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)


def load(monkeypatch, **env):
    """Import poc.ask_server fresh, because its config is read at import time."""
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    sys.modules.pop("poc.ask_server", None)
    import importlib
    return importlib.import_module("poc.ask_server")


def make_repo(path):
    os.makedirs(path, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)


# --- repo_paths -------------------------------------------------------------------------
# Failure prevented: the bridge silently answering about ZERO repositories (or about a
# directory that is not a checkout) because the machine keeps its clones somewhere else.

def test_repo_paths_takes_explicit_list_across_locations(tmp_path, monkeypatch):
    a = tmp_path / "work" / "HA"
    b = tmp_path / "elsewhere" / "monitor"
    make_repo(str(a))
    make_repo(str(b))
    m = load(monkeypatch, ASK_REPOS="%s;%s" % (a, b), ASK_ROOT=str(tmp_path))
    assert m.repo_paths() == [str(a), str(b)]


def test_repo_paths_drops_a_path_that_is_not_a_checkout(tmp_path, monkeypatch):
    a = tmp_path / "HA"
    make_repo(str(a))
    plain = tmp_path / "just_a_folder"
    plain.mkdir()
    m = load(monkeypatch, ASK_REPOS="%s;%s;%s" % (a, plain, tmp_path / "missing"),
             ASK_ROOT=str(tmp_path))
    assert m.repo_paths() == [str(a)]


def test_repo_paths_falls_back_to_scanning_the_root(tmp_path, monkeypatch):
    make_repo(str(tmp_path / "one"))
    make_repo(str(tmp_path / "two"))
    (tmp_path / "three").mkdir()
    m = load(monkeypatch, ASK_REPOS="", ASK_ROOT=str(tmp_path))
    assert [os.path.basename(p) for p in m.repo_paths()] == ["one", "two"]


# --- age_phrase -------------------------------------------------------------------------
# Failure prevented: reporting a stale repository as fresh (or crashing on a git date format),
# which is exactly the case this whole freshness check exists for.

def test_age_phrase_units(monkeypatch):
    m = load(monkeypatch)
    now = datetime.now()
    assert m.age_phrase((now - timedelta(minutes=7)).strftime("%Y-%m-%d %H:%M:%S +0200")) == "7 min temu"
    assert m.age_phrase((now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S +0200")) == "5 h temu"
    assert m.age_phrase((now - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S +0200")) == "4 dni temu"


def test_age_phrase_survives_garbage(monkeypatch):
    m = load(monkeypatch)
    assert m.age_phrase("nie data") == "nieznany czas"
    assert m.age_phrase(None) == "nieznany czas"


# --- context_block ----------------------------------------------------------------------
# Failure prevented: the model getting the repository state but no instruction to admit
# staleness out loud - the driver would hear a confident answer from yesterday's tree.

def test_context_block_carries_every_line_and_the_instruction(monkeypatch):
    m = load(monkeypatch)
    block = m.context_block(["HA: podciagniete", "monitor: NIE odswiezone"])
    assert "HA: podciagniete" in block
    assert "monitor: NIE odswiezone" in block
    assert "NIE odswiezone" in block and "sprzed" in block
    assert block.rstrip().endswith("PYTANIE:")


def test_sync_disabled_says_so_instead_of_pretending(tmp_path, monkeypatch):
    make_repo(str(tmp_path / "one"))
    m = load(monkeypatch, ASK_SYNC="0", ASK_ROOT=str(tmp_path), ASK_REPOS="")
    assert m.sync_all(1) == ["synchronizacja wylaczona"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
