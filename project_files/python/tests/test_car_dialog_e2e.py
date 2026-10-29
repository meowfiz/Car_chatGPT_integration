"""Testy czystych funkcji runnera e2e dialogu auta (poc/car_dialog_e2e.py)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "poc"))
import car_dialog_e2e as e  # noqa: E402


def test_tabela_ma_wszystkie_wiersze():
    """Porazka: zmiana formatu tabeli cicho gubi scenariusze i e2e przechodzi na pustym."""
    rows = e.parse_table(open(e.TABLE, encoding="utf-8").read())
    assert len(rows) >= 30
    assert [r["n"] for r in rows] == sorted(r["n"] for r in rows)


def test_parse_state():
    assert e.parse_state("main") == ("main", None, None)
    assert e.parse_state("W(Car,praca)") == ("window", "Car", "praca")
    assert e.parse_state("main + pending(machine)") is None


def test_check_zly_outcome_i_stan():
    res = {"outcome": "answered", "state": {"mode": "main"}, "text": "x"}
    bad = e.check(res, ["moved"], ("window", "Car", None), [])
    assert len(bad) == 3  # outcome, mode, project


def test_check_zgodny_z_diakrytykami():
    res = {"outcome": "moved", "state": {"mode": "window", "project": "Car_chatGPT_integration",
                                         "machine": "praca"}, "text": "Jesteś w oknie Car w pracy"}
    assert e.check(res, ["moved"], ("window", "Car", "praca"), e.quoted("„jesteś”")) == []


def test_outcomes_lub():
    assert e.outcomes("queued lub answered") == ["queued", "answered"]


def test_bez_live_nie_wysyla_do_okna():
    """Porazka z 2026-10-29: e2e wpisal tekst do zywego okna HA. queued = wpis do okna."""
    assert e.sends_to_window(["queued", "answered"])
    assert not e.sends_to_window(["moved", "pending"])
    assert not e.sends_to_window(["where"])
