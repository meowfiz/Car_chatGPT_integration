"""Z28 pomiar M1/M2 wrappera _resolve_window_with_aliases.

Prerejestracja: openspec/changes/carplay-okna-projektow/tasks.md pkt 2c.17 (commit 90e784a).

Procedura (ZASADY 3.3, 5.3):
1. Kontrola odtworzenia P2: wrapper z PUSTYM cache aliasow musi zwrocic DOKLADNIE to co
   okna.resolve solo dla wszystkich 49 fraz (zbior A: 39 par + zbior B: 10 fraz). Jesli
   nie -- skrypt ODMAWIA uruchomienia pomiaru glownego.
2. Pomiar M1: wrapper z WYPELNIONYM cache (z Orchestratora) -- ile z 39 par rozwiazuje
   do kanonu. Prog 39/39.
3. Pomiar M2: wrapper z wypelnionym cache -- ile z 10 fraz zbioru B zachowuje puste
   zwroty. Prog 10/10.
4. Decyzja wg prerejestracji.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAR = os.path.dirname(HERE)
ALIASES_PATH = os.path.join(HERE, "aliases.json")
PI_TOOLS = os.path.normpath(os.path.join(CAR, "..", "project_integration", "tools"))
sys.path.insert(0, PI_TOOLS)

import voice_gateway as vg  # noqa: E402
import okna as okna_mod  # noqa: E402


def load_zbior_A():
    """3 frazy na projekt z poc/aliases.json (nie wszystkie, zeby bylo dokladnie 39 par)."""
    with open(ALIASES_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    pairs = []
    for canon, aliases in data["repos"].items():
        for alias in aliases[:3]:  # pierwsze 3
            pairs.append((alias, canon))
    return pairs


ZBIOR_B = [
    "jakis losowy projekt",
    "cos czego nie ma",
    "panda",
    "prosze o pomoc",
    "co teraz",
    "kot domowy",
    "programowanie w rust",
    "wczoraj spadal snieg",
    "nic takiego",
    "siedem dziewiec",
]


def resolver_solo(repo_names):
    def _r(q):
        return okna_mod.resolve(q, repo_names)
    return _r


def kontrola_odtworzenia(repo_names, zbior_A, zbior_B):
    """P2: wrapper z pustym cache = resolver solo dla wszystkich 49 fraz."""
    # Pusty cache: ts=0.0, data=None. api wyrzuci wyjatek (localhost moze dzialac,
    # wiec symulujemy brak przez monkey-set).
    vg._CAR_ALIASES_CACHE["ts"] = 0.0
    vg._CAR_ALIASES_CACHE["data"] = None
    orig_api = vg.api
    try:
        vg.api = lambda *a, **k: (_ for _ in ()).throw(ConnectionError("P2 symulacja"))
        rozjazdy = []
        wszystkie = [a for a, _ in zbior_A] + list(zbior_B)
        resolver = resolver_solo(repo_names)
        for fraza in wszystkie:
            with_wrapper = vg._resolve_window_with_aliases(fraza, resolver)
            solo = resolver(" ".join(fraza.lower().split()))
            if with_wrapper != solo:
                rozjazdy.append((fraza, with_wrapper, solo))
        return rozjazdy
    finally:
        vg.api = orig_api


def pomiar_M1_M2(repo_names, zbior_A, zbior_B):
    """Pomiar glowny: wrapper z aliasami z pliku."""
    # Zbuduj cache alias_map bez wywolywania Orchestratora, zeby test byl deterministyczny
    with open(ALIASES_PATH, "r", encoding="utf-8") as fh:
        aliases_data = json.load(fh)
    alias_map = {}
    for canon, aliases in aliases_data["repos"].items():
        for alias in aliases:
            if isinstance(alias, str):
                key = " ".join(alias.lower().split())
                if key:
                    alias_map[key] = canon
    import time as _time
    vg._CAR_ALIASES_CACHE["ts"] = _time.time()
    vg._CAR_ALIASES_CACHE["data"] = alias_map

    resolver = resolver_solo(repo_names)
    # M1
    m1_hit = 0
    m1_misses = []
    for fraza, kanon in zbior_A:
        out = vg._resolve_window_with_aliases(fraza, resolver)
        if out == [kanon]:
            m1_hit += 1
        else:
            m1_misses.append((fraza, kanon, out))
    # M2
    m2_hit = 0
    m2_misses = []
    for fraza in zbior_B:
        out = vg._resolve_window_with_aliases(fraza, resolver)
        if out == []:
            m2_hit += 1
        else:
            m2_misses.append((fraza, out))
    return (m1_hit, len(zbior_A), m1_misses, m2_hit, len(zbior_B), m2_misses)


def main():
    # Repo names z monitor_repos.env
    env = os.path.join(os.path.expanduser("~"), ".claude", "monitor_repos.env")
    repos = okna_mod.parse_repos(okna_mod.read_text(env))
    repo_names = list(repos.keys())
    zbior_A = load_zbior_A()
    zbior_B = ZBIOR_B

    print("Z28 pomiar wrappera aliasow")
    print("Zbior A: %d par, Zbior B: %d fraz" % (len(zbior_A), len(zbior_B)))
    print()
    print("Kontrola odtworzenia P2 (ZASADY 5.3)...")
    rozjazdy = kontrola_odtworzenia(repo_names, zbior_A, zbior_B)
    if rozjazdy:
        print("P2 FAIL: %d rozjazdow (wrapper z pustym cache != okna.resolve solo)" %
              len(rozjazdy))
        for fraza, w, s in rozjazdy[:5]:
            print("  %r -> wrapper=%r, solo=%r" % (fraza, w, s))
        print("ODMAWIAM uruchomienia pomiaru glownego (ZASADY 5.3)")
        return 1
    print("P2 OK: wrapper z pustym cache == okna.resolve solo dla 49/49 fraz")
    print()

    m1_hit, m1_total, m1_misses, m2_hit, m2_total, m2_misses = pomiar_M1_M2(
        repo_names, zbior_A, zbior_B)

    print("M1: %d/%d par z Zbior A rozwiazuje sie do kanonu (prog 39/39)" %
          (m1_hit, m1_total))
    if m1_misses:
        print("  misses:")
        for fraza, kanon, out in m1_misses[:5]:
            print("    %r (oczekiwano %r, got %r)" % (fraza, kanon, out))
    print("M2: %d/%d fraz z Zbior B zachowuje pusty zwrot (prog 10/10)" %
          (m2_hit, m2_total))
    if m2_misses:
        print("  misses:")
        for fraza, out in m2_misses:
            print("    %r -> %r" % (fraza, out))

    # Decyzja wg prerejestracji
    print()
    neg = (m1_hit < m1_total) or (m2_hit < m2_total)
    if m1_hit == m1_total and m2_hit == m2_total:
        print("DECYZJA: ZALICZONE (M1=%d/%d, M2=%d/%d)" %
              (m1_hit, m1_total, m2_hit, m2_total))
        return 0
    elif neg:
        print("DECYZJA: NEGATYW (warunek NEGATYWU aktywny) -- nie stroje do magic konstanty")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
