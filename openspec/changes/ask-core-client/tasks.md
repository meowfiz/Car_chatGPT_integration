## 1. Zależność od rdzenia

- [ ] 1.1 Sprawdzić, że `monitor/ask_core.py` jest w tym repo (dostarcza `install_pack.py` z `project_integration`); jeśli nie ma — `python tools/install_pack.py <to repo> --apply` po stronie monitora i `git pull`
- [ ] 1.2 PREREJESTRACJA pomiaru: przed zmianą zmierzyć obecne 10 pytań (mediana i p90 pełnej pętli oraz samego `claude`), zapisać w notatce; warunek negatywu: jeśli po przejściu na rdzeń mediana rośnie o > 15%, wracamy do własnego `ask_claude` i mówimy dlaczego

## 2. Przeniesienie świeżości do rdzenia (nasz wkład)

- [ ] 2.1 `sync_repo` → `ask_core.refresh_repo(path, timeout)` bez zmiany semantyki: `pull --ff-only` tylko przy czystym drzewie, nigdy rebase, nigdy push; zwraca stan („podciagniete z remote" / „bez zmian na remote" / „lokalne zmiany, nie odswiezam" / „NIE odswiezone")
- [ ] 2.2 `sync_all` → `ask_core.refresh_all(paths, timeout)` (równolegle, jak dziś: zmierzone 1,95 s dla czterech repo)
- [ ] 2.3 Testy z `project_files/python/tests/test_ask_server.py` dotyczące świeżości przenieść do paczki razem z kodem; tutaj zostaje test, że `ask_server` **woła** rdzeń (a nie że rdzeń działa)

## 3. `ask_server.py` jako klient

- [ ] 3.1 `ask_claude(question)` → `ask_core.ask(REPOS, question, system=SYSTEM, model=MODEL, timeout=CLAUDE_TIMEOUT)`; `SYSTEM` (kierowca: trzy zdania, bez markdown) zostaje w tym repo jako parametr
- [ ] 3.2 `for_speech` → `ask_core.for_speech`; usunąć lokalną kopię po potwierdzeniu, że testy na bloki kodu i znaki markdown przechodzą na wersji z rdzenia
- [ ] 3.3 `repo_paths()`: domyślnie `~/.claude/monitor_repos.env`, `ASK_REPOS` / `ASK_ROOT` jako nadpisanie; test: pusta mapa i brak zmiennych → czytelny błąd, nie cisza
- [ ] 3.4 Sprawdzić na tej maszynie, że pytanie z limitem („w dwóch zdaniach") rzeczywiście dociera do modelu — rdzeń przekazuje pytanie przez **stdin**, nie w argv (defekt monitora z 2026-09-16); test: żaden element argv nie zawiera `\n`
- [ ] 3.5 Powtórzyć pomiar 1.2 i porównać z prerejestracją; liczby w notatce sesji

## 4. Jeden rezydent na maszynę

- [ ] 4.1 `poc/deploy/02_install_tasks.ps1`: dodatkowe zadanie „przy logowaniu" → `python <repo>\monitor\ask_worker.py --spawn` (idempotentne: worker sam sprawdza blokadę i wychodzi, gdy inny działa)
- [ ] 4.2 `poc/deploy/check_bridge.ps1`: pokazać też stan workera (`ask_worker.py --status`)
- [ ] 4.3 `poc/deploy/README_PRACA.md`: jeden akapit, że pecet w pracy odpowiada wtedy **obiema** drogami — głosem z auta i na pytania z Home Assistanta

## 5. Domknięcie

- [ ] 5.1 Notatka sesji z liczbami (przed/po) i wpis w `notes/start.md`
- [ ] 5.2 Zaznaczyć w `project_integration/openspec/changes/ask-core/tasks.md` zadania 2.2 i 2.3 jako zrobione po stronie klienta
