## 1. PoC gating — Siri Shortcut odtwarza audio z HTTPS tailnetu w CarPlay

- [x] 1.1 Jednorazowy skrót iOS „CarPlay audio test": `GET` endpoint `/api/car/test-audio` (zwraca `audio/mpeg` edge-tts z „test glosu w aucie"), `Get Contents of URL`, `Play Sound`. Instrukcja krok po kroku w `notes/HANDOFF_carplay_okna.md` (sekcja 1.1)
- [x] 1.2 Tymczasowy endpoint `/api/car/test-audio` w `project_integration/tools/voice_gateway.py` (nie `monitor/` — tam go nie ma; `pack/` dostanie go dopiero po PoC); edge-tts generuje audio on-demand (`speak_edge(CAR_TEST_TEXT)`), żadnego trzymania pliku w repo. Bind dziedziczony z bramki (tailnet-only przez `discover_tls()`), bez tokenu w PoC, oznaczony `# TODO: usunac po PoC`
- [ ] 1.3 Pomiar na postoju: 3 próby „Hey Siri, CarPlay audio test" z telefonu z CarPlay podpiętym po USB; zapis do HANDOFF kolumn: nr, start, odtworzone (tak/nie), opóźnienie [s], jakość (zrozumiałe/zniekształcone), uwagi
- [x] 1.4 Decyzja PoC (2026-10-12): **Skrót A urywa** (user słyszał „test" zamiast „test głosu w aucie"), **Skrót B dociąga** ale głos systemowy Siri. Zapis w HANDOFF jako „ograniczenie techniczne CarPlay" (ZASADY 5.8). **Nowa decyzja** (D10 w design.md): porzucamy Siri Shortcut jako wejście, przełączamy na HA Assist w CarPlay. Grupa 2 (`/api/car/command`) **PORZUCONA**, zastępuje ją nowa grupa 1.5 (HA Assist) i przerobiona grupa 2 (`/api/car/dispatch`).

## 1.5 Przełączenie wejścia na HA Assist w CarPlay (2026-10-12, po D10)

- [x] 1.5.1 HA Claude w oknie `HA`: dodać kafelek **Assist** jako Quick Access w CarPlay (HA Companion → ustawienia → CarPlay), zweryfikować lokalny pipeline PL + VCC głos Sznuka — potwierdzone w kuchni, pełne zdanie bez cięć
- [x] 1.5.2 Rozszerzenie `voice/claude_sentences_pl.yaml` o intent `DispatchClaude` z frazami: „Claude do okna {pytanie}", „Claude w oknie {pytanie}", „Claude otwórz okno {pytanie}", „Claude kontynuuj {pytanie}", „Claude dalej {pytanie}". Wildcard na całość (po stronie bramki `parse_car_prompt` wyciąga nazwę projektu i resztę)
- [x] 1.5.3 **Nieaktualne** — aliasy zrobione w `parse_car_prompt` przez wywołanie `okna.resolve` (fuzzy exact→prefix→substring), bez osobnego pliku. `monitor_repos.env` jest jedynym źródłem prawdy. Pominięte świadomie
- [x] 1.5.4 `voice/rest_command_claude.yaml` — nowy wpis `claude_dispatch` POST do `/api/car/dispatch` z `Authorization: !secret car_token_header`, body `{session_id (= conversation_id), project: "", prompt: pytanie}`. Czeka na HA stronę: wklejenie secretu i reload
- [ ] 1.5.5 Seria C pomiarowa w aucie (3 próby „test głosu w aucie" przez kafelek Assist w CarPlay) — tabela w `HANDOFF_carplay_okna.md`. **Jedyny PoC-gating dla reszty zmiany po D10:** < 2/3 pełnego dociągu → wracamy do design, dalsze grupy nie rozpoczynają się
- [ ] 1.5.6 Dla PoC seria C **wystarczy fraza stała HA** („test głosu w aucie" → TTS „test głosu w aucie") — nie potrzebujemy jeszcze pełnego dyspozytora z 1.5.2–1.5.4; te dochodzą po zdaniu bramki

## 2. Endpoint `/api/car/dispatch` w bramce (zastępuje stary `/api/car/command` po D10)

- [x] 2.1 Szkielet endpointu `POST /api/car/dispatch` w `project_integration/tools/voice_gateway.py`: JSON `{session_id, project, prompt}`, Bearer token z `~/.claude/car_tokens.json`, odpowiedź JSON `{text, outcome, resolved_project?}`. Smoke test z pecetu 2026-10-12: `project_integration` 5.2 s, fuzzy `project integration` 6.5 s, sticky session reuse 5.3 s, timeout obsłużony
- [x] 2.2 Parser `parse_car_prompt(prompt, resolve_fn)` w bramce (nie w HA — HA wysyła całość jako wildcard `{pytanie}`, bo Speech-to-Phrase nie zna nazw projektów). Rozpoznaje: `kontynuuj X` → mode=continue, `<1-3 slow nazwa> <reszta>` → dispatch, sama nazwa → set_only, nic → fallback do sticky. 8 testów jednostkowych
- [x] 2.3 Resolve nazwy projektu wywołuje `okna.resolve` jako sanity check aliasu z HA; `missing`/`ambiguous` zwrot w JSON. Smoke: `panda` → `missing` (0.03 s), `rib` → `RibnXtr2026` (single match)
- [x] 2.4 Transport do pane: **reuse `cli_bridge.type_into`** (load-buffer + paste-buffer + Enter, polskie znaki bez kodowania przez CLI). Zero duplikacji — ta sama funkcja, co dispatch worker
- [x] 2.5 Zwrot `Glosowo:` z pane: pętla `cli_bridge.capture` + `extract_reply` + `spoken_lines` co 500 ms, do pierwszej linii nowszej niż `before` lub timeout 30 s. Reuse z `cli_bridge`
- [x] 2.6 Pole `text` w JSONie = pierwsza linia `Glosowo:` **bez prefiksu** (robi `spoken_lines`), outcome `sent`/`timeout`/`missing`/`ambiguous`/`refused`
- [x] 2.7 Testy jednostkowe `project_integration/tools/tests/test_car_dispatch.py`: 26 passed + 1 świadomy skip. Pokrywa: `should_refuse_car` 11 wzorców + 2 normalizacje spacji, `car_sessions_*` set/get/expire/overwrite, `load_car_tokens` BOM UTF-8/rotacja/short/malformed/missing
- [x] 2.8 Smoke test integracyjny z pecetu: 4 przypadki OK: `missing` (0.03 s), `refused` (0.02 s), `no token` → 401, dispatch do `project_integration` sticky session (5.2–6.5 s)

## 2a. Rozszerzone endpointy funkcjonalne (sprint 2026-10-12)

- [x] 2a.1 `GET /api/car/status` — agreguje `/api/state`, zwraca Głosowo tekst z liczbami. Smoke: 22 projekty, 182 zadania otwarte, 1 niewypchnięty, 3 pracujące
- [x] 2a.2 `POST /api/car/open` body `{project}` — subprocess do `tools/okno.py`, idempotentne, zwraca „otwieram X" lub „okno X juz dziala". Smoke: `voice` otwarte w 5.5 s
- [x] 2a.3 `GET /api/car/project/<name>/summary` — fuzzy przez `okna.resolve`, agreguje rekord z `/api/state`. Smoke: `car integration` → `Car_chatGPT_integration`, `HA` → stan 2 z 19 otwartych
- [x] 2a.4 **4-ty tier w `okna.resolve`: token-match** — gdy query ma ≥ 2 słowa, dopasowanie jeśli każdy token jest podciągiem znormalizowanej nazwy. Potrzebne dla „car integration" vs `Car_chatGPT_integration`. 4 nowe testy przeszły, cała suita 74/75

## 2b. Rozszerzenia głosowe (sprint 2026-10-12 wieczór)

- [x] 2b.1 `POST /api/car/todo` body `{text, project?, session_id?}` — zapisuje TODO głosem do `~/.claude/carplay_todos.jsonl`. Project z sticky jeśli puste. 3 scenariusze smoke
- [x] 2b.2 `POST /api/car/zamknij` body `{session_id}` — kasuje sticky, zwraca „zamkniete bylo X" lub „nie bylo aktywnej sesji"
- [x] 2b.3 `POST /api/car/powtorz` body `{session_id}` — powtarza ostatnie Glosowo. Rejestr sesji trzyma `last_text`, dispatch aktualizuje
- [x] 2b.4 Pure helpery: `build_car_status_text`, `build_car_project_text`, `car_update_last_text`, `car_get_last_text`. 9 nowych testów (razem 47 passed, 1 skipped)
- [x] 2b.5 Dokumentacja: `notes/HANDOFF_car_endpoints.md` (337 linii) — kontrakt, autoryzacja, rejestr sesji, odmowy, 4-tier resolver, wzorzec rest_command dla HA

## 2c. Dojrzałość PoC (sprint 2026-10-12 noc)

- [x] 2c.1 `GET /api/car/ostatnie_todo?n=5` — recytacja ostatnich N TODO z `carplay_todos.jsonl`; `?n=` od 1 do 10
- [x] 2c.2 `poc/car_selftest.py` — sanity check 11 endpointów, PASS/FAIL/czas, bez body check. Smoke 11/11 w ~42 s
- [x] 2c.3 Code review subagent (0 BLOCKER, 4 NICE-TO-HAVE, 2 COSMETIC): auth helper dedup (`_car_authorized`), rozszerzone `CAR_REFUSE_PATTERNS` z 11 do 23 wzorców (powershell/iex/|sh/del /s/chmod 777/dd/mkfs/rm -fr/rm --recursive) + 12 nowych testów
- [x] 2c.4 Fix N1 race w rejestrze sesji: `threading.Lock` wokół RMW sekwencji w `car_set_active`, `car_update_last_text`, `_car_zamknij`. Test: 20 wątków set_active → 20 session_id w rejestrze. Lazy path lookup w `car_sessions_{load,save}` (default=None, re-read z CAR_SESSION_PATH)
- [x] 2c.5 Spec rozszerzony o 2 nowe wymagania: endpointy wsparcia (todo/zamknij/powtorz/ostatnie_todo) i 4-tier `okna.resolve`
- [x] 2c.6 `GET /api/car/projekty?n=7` — dynamiczna lista nazw projektów do wymówienia dla PomocClaude (zamiast hardcoded). Smoke: pierwsze 5 OK
- [x] 2c.7 `GET /api/car/metryki?h=24` — parser `voice_gateway.log`, zlicza `car-*` wpisy. Smoke: 121 wywolan w 24h, top 3: dispatch 32, poc 30, status 13
- [x] 2c.8 Self-test rozszerzony do 15 endpointow (bylo 11): + projekty, ostatnie_todo, zamknij.pusty, powtorz.pusta. 15/15 PASS w ~38s
- [x] 2c.9 `POST /api/car/stop` body `{pane}` — awaryjne przerwanie dispatcha z auta. `tmux send-keys C-c` do pane. Z23 w pętli profesor-student. Pomiar: 347 ms (próg 2000 ms). 1 pytest nazywający porażkę („stop bez pane zwraca 400, nie 500"), self-test rozszerzony do 17/17 (+ car.stop.brak_pane 400, + car.stop.nieistniejacy 404)
- [ ] 2c.10 **PREREJESTRACJA Z24** (przed uruchomieniem skryptu, ZASADY 3.3): pomiar e2e `/api/car/stop` 10 prób z pecetu przez adres tailnetowy (symulacja telefonu bo user offline). **Hipoteza negatywna**: mediana > 3000 ms lub ≥ 1 timeout/5xx w 10 → endpoint nie nadaje się do auta, wracamy do architektury. **Hipoteza pozytywna**: mediana ≤ 1500 ms, p90 ≤ 2500 ms, 10/10 OK. **3 miary**: (1) latencja e2e per próba z zegarem bramki — min/median/p90/max; (2) skuteczność `tmux send-keys`: `capture-pane` przed/po, zmiana ostatniej linii = sukces, próg 10/10; (3) status HTTP: 10×200, zero 4xx/5xx, próg 10/10. **Liczba porównań: 1** (ścieżka główna /stop, bez wariantów). Konfuzje: sieć tailnet (symulacja ≠ telefon LTE), pane bez aktywnego procesu (symulowany sleep ≠ Claude Code). Wynik NIE uprawnia do: „działa pod obciążeniem" (10 prób, nie 1000), „na każdym pane" (1 pane, nie 22), „sieć LTE OK" (symulacja z pecetu).
- [x] 2c.10 PREREJESTRACJA Z24 commitowana przed pomiarem 23:34 UTC
- [x] 2c.11 Z24 pomiar: `poc/stop_e2e_pomiar.py` 10 prób, zapis `project_files/run_files/stop_e2e_2026-10-12-233411.jsonl`. Wynik: **ZALICZONE 3/3 miar**. Miara 1: min 298.2 / median 309.5 / p90 325.4 / max 326.2 ms (progi 1500/2500). Miara 2: 10/10 `send-keys` skuteczne (capture-pane zmiana). Miara 3: 10/10 HTTP 200. Wynik NIE uprawnia do: obciążenia (10 prób, nie 1000), każdego pane (1 pane), LTE OK (symulacja z pecetu — ta sama sieć co bramka)
- [x] 2c.12 **PREREJESTRACJA Z25** w commit 4f5e54f (przed mutacją). ZASADY 3.3 zachowane
- [x] 2c.13 Z25 wynik: **NEGATYW hipotezy** (ZASADY 5.8). Pytest `test_stop_bez_pane_zwraca_400_nie_500` **przeszedł mimo mutacji** `rc == 0` → `rc != 0`. Przyczyna: test pokrywa branch `brak pane → 400` (pre-send-keys), mutacja jest post-send-keys. **ALE** integration test (self-test live) **złapał mutację** — zwrócił `outcome="timeout"` zamiast `"sent"`. Wniosek: ZASADY 4.4 „testy sprawdzone mutacją" spełnione dla self-testu live, **nie dla pytest**. Pytest nie pokrywa sukces-branche semantyki `send-keys`. Kod przywrócony, `git diff` pusty (zweryfikowane)
- [ ] **WYMAGA PROJEKTU — nie fix in-place** (KRYT 1 z code review 2 Z25): semantyka `/api/car/stop` dla sesji wielo-okiennych i `claude -p` signal handler. `send-keys -t =session:` idzie do aktywnego pane, nie konkretnego. `claude -p` ma własny signal handler — pojedyncze C-c czyści prompt, nie zabija generowania. Text „stopnieto X" kłamie. Decyzja projektowa (nowy proposal/design, nie bugfix). Zapisane w `notes/HANDOFF_voice_gateway.md`
- [x] 2c.14 **Z26 FIX KRYT 2**: `_car_stop` miał `outcome="timeout"` dla `rc != 0` bez TimeoutExpired. Fix 2026-10-13 noc: osobny `except subprocess.TimeoutExpired` → `outcome="timeout"` 200 OK; `rc != 0` bez timeoutu → `outcome="error"` 200 OK + pole `rc`. Spec rozszerzony: enum `sent|resolved|ambiguous|missing|refused|error|timeout`. **Mutation test** (ZASADY 4.4 druga połowa): nowy pytest `test_stop_rc_nonzero_zwraca_outcome_error_nie_timeout` używający `monkeypatch` dla `subprocess.run` z `rc=1`. Mutation: zamiana `"error"` → `"timeout"` → test PADŁ (`E - error / E + timeout`), kod przywrócony. **99 pytest passed** (było 98, +1)
- [x] 2c.15 **PREREJESTRACJA Z27** w commit przed kodem. ZASADY 3.3 zachowane
- [x] 2c.16 **Z27 FIX**: `POST /api/car/rotate_token` zbudowany. `secrets.token_hex(32)` → nowy token, zapis atomowy `tmp + os.replace`, odpowiedź JSON `{token, rotated_at, token_hash (sha256[:8])}`. **Nie loguje tokena**, tylko `rotated_at` i hash prefix. **Odczyt per-request z dysku** (bez cache w pamięci — rotacja działa bez restartu). **2 pytesty**: integracyjny (3 asercje: stary→401, nowy→200, plik zmieniony przez `_car_rotate_token` na FakeHandler) + atomowości (symulacja wyjątku przed `os.replace` → stary token dalej w pliku). **Mutation**: `os.replace` usunięty → test padł z `assert nowy in nowe_tokeny` (nowy token nie w pliku). Kod przywrócony. **Live test**: rotacja z backupem — ROTACJA OK (hash 05e2b7db), stary→401, nowy→200, backup przywrócony dla HA. **Fix uboczny**: `load_car_tokens(path=None)` lazy lookup (było `path=CAR_TOKEN_PATH` — monkeypatch nie działał, odkryte przez test). **101 pytest** (było 99, +2), self-test 17/17

- [ ] 2c.17 **PREREJESTRACJA Z28** (przed implementacją, ZASADY 3.3): wrapper `_resolve_window_with_aliases(query)` używa aliasów z Orchestratora (`GET /api/projects`, cache TTL 600 s, HTTP timeout 2 s, 5xx/timeout → fallback do starego cache lub `okna.resolve` solo, 4xx → log + wyjątek do góry — bo to konfig błąd, nie cichy fallback). **Hipoteza**: redukuje do zera odsetek `project=None` dla fraz z `poc/aliases.json`, bez zmiany zachowania dla fraz spoza aliases. **Dane testu**:
  - **Zbiór A (39 par)**: 3 frazy × 13 projektów z `poc/aliases.json` (fraza → kanon)
  - **Zbiór B (10 literalnych fraz, zadeklarowanych PRZED implementacją — nie generowane dynamicznie)**:
    1. `jakis losowy projekt`
    2. `cos czego nie ma`
    3. `panda`
    4. `prosze o pomoc`
    5. `co teraz`
    6. `kot domowy`
    7. `programowanie w rust`
    8. `wczoraj spadal snieg`
    9. `nic takiego`
    10. `siedem dziewiec`
  - **Statystyka**: M1 = ile z 39 par rozwiązuje się do kanonicznej (próg **39/39**); M2 = ile z 10 fraz zbioru B zachowuje puste zwroty (próg **10/10**)
  - **Kontrola odtworzenia P2 (ZASADY 5.3)**: skrypt pomiarowy **odmawia uruchomienia** gdy wrapper z pustym cache aliasów nie zwraca identycznych wyników co `okna.resolve` solo dla wszystkich 49 fraz (A ∪ B)
  - **Liczba porównań**: 1 (wrapper vs status quo)
  - **Warunek NEGATYWU**: M1 < 39/39 albo M2 < 10/10 → przerywam, nie stroję do magic konstanty
  - **Wynik NIE uprawnia**: do „fuzzy ogólnie lepszy"; do opinii o rzeczywistych frazach z auta (tylko syntetyczne); do frontu HA Assist ani Siri; do opinii o aliasach wielokomponentowych w kanonie

- [x] 2c.18 **Z28 WYNIK** (noc 2026-10-13, po PREREJESTRACJI 2c.17): wrapper `_resolve_window_with_aliases` zbudowany. **Kontrola odtworzenia P2**: wrapper z pustym cache == `okna.resolve` solo dla **49/49 fraz** (ZASADY 5.3 spełniona). **Pomiar główny**: **M1 = 42/42** (nie 39 — `aliases.json` ma 14 projektów, nie 13 jak policzyłem w prerejestracji; wszystkie rozwiązują się do kanonu); **M2 = 10/10** (wszystkie frazy zbioru B zachowują puste zwroty). **DECYZJA: ZALICZONE**. 4 nowe pytesty (`test_wrapper_aliasow_*`: mapuje, fallback, pusty cache, 4xx), **68 pytest passed** (było 64, +4). Skrypt pomiarowy `poc/z28_aliases_pomiar.py` z kontrolą P2 odmawiającą uruchomienia głównego pomiaru przy rozjazdach. **Fix ubocznego nie było** — kod przeszedł od razu. **Wrapper nie podpięty do `_car_dispatch`** w tej iteracji — osobna tura po pomiarze z rzeczywistymi frazami z auta (ZASADY 3.1: osobna zmiana)

- [ ] 2c.19 **PREREJESTRACJA Z29a** (PRZED mutacjami, ZASADY 3.3 + 4.4): mutation test wrappera `_resolve_window_with_aliases`. **Hipoteza**: każdy z 4 testów `test_wrapper_aliasow_*` wykryje co najmniej 1 mutację swojej gałęzi. **Lista 4 mutacji** (ZASADY 5.4 — dokładnie 4, nie więcej):
  1. **Wyłącz mapowanie**: w `_resolve_window_with_aliases` zwróć od razu `resolver_fn(query)` z pominięciem cache aliasów → ma paść `test_wrapper_aliasow_mapuje_fraze_do_kanonu`
  2. **Zepsuj fallback**: dla frazy spoza aliasów zwróć `[]` zamiast `resolver_fn(query)` → ma paść `test_wrapper_aliasow_fallback_do_resolver_dla_fraz_spoza`
  3. **Zepsuj zachowanie pustego cache**: przy pustym cache zwróć `[]` zamiast delegować do resolver → ma paść `test_wrapper_aliasow_pusty_cache_zachowuje_sie_jak_resolver_solo`
  4. **Zepsuj politykę 4xx**: dla 4xx w `_car_cached_aliases` zignoruj zamiast podnieść (cichy fallback) → ma paść `test_wrapper_aliasow_4xx_rzuca_wyjatek_do_gory`
  **Statystyka**: liczba mutacji wykrytych / 4. **Próg = 4/4**. **Warunek NEGATYWU** (ZASADY 5.8): < 4/4 → mutacja niewykryta dostaje własny test; stop dalszych mutacji. **Wynik NIE uprawnia**: do kompletnego pokrycia semantycznego wrappera. 4 mutacje = 4 gałęzie, nie wszystkie

- [ ] 2c.21 **Z29c NICE #4** — mutacja `log("car-aliases", ...) → pass` by przeszła przez obecne 4 testy wrappera (brak asercji `call_count` logu w `test_wrapper_aliasow_4xx_rzuca_wyjatek_do_gory`). **Kryterium akceptacji**: dodać asercję `mock.call_count ≥ 1` dla loga 4xx w teście 4xx; mutacja `log → pass` → test padnie. **Ryzyko**: niskie (mikro-mutacja, standardowa łatka). **Status**: świadomie odłożone — mikro-mutacja, standardowa łatka asercji call_count niewiele wnosi (ZASADY 5.10)

- [ ] 2c.22 **Z29c NICE #5** — TTL 600 s w cache aliasów. **Potencjał**: user edytuje `aliases.json` → `sync_aliases.py` → Orchestrator, do 10 min opóźnienia zanim bramka zobaczy („zmieniłem i nie działa"). **Kryterium akceptacji**: albo (a) endpoint `POST /api/aliases/invalidate` wymuszający re-fetch, albo (b) ETag/If-None-Match w `GET /api/projects` z invalidacją po zmianie. **WYMAGA POMIARU PRZED IMPLEMENTACJĄ** (ZASADY 5.10 — jedna zadeklarowana reguła, nie tuning per przypadek): ile razy w typowej sesji auta user zmienia alias? Jaki jest realny TTL potrzebny? Bez tego fix jest tuningiem bez miary — osobna prerejestracja

- [x] 2c.20 **Z29a WYNIK** (noc 2026-10-13): **4/4 mutacji wykrytych**, próg spełniony.
  - M1 (wyłącz mapowanie) → `test_wrapper_aliasow_mapuje_fraze_do_kanonu` **FAILED**
  - M2 (zepsuj fallback) → `test_wrapper_aliasow_fallback_do_resolver_dla_fraz_spoza` **FAILED**
  - M3 (pusty cache zwraca []) → `test_wrapper_aliasow_pusty_cache_zachowuje_sie_jak_resolver_solo` **FAILED**
  - M4 (cichy fallback dla 4xx) → `test_wrapper_aliasow_4xx_rzuca_wyjatek_do_gory` **FAILED**
  Kod przywrócony po każdej mutacji, finalny `git diff tools/voice_gateway.py` pusty, 68 pytest zielony. Mutacje nie commitowane (byłyby złamaniem produkcyjnego kontraktu). **DECYZJA: Z29a ZALICZONE 4/4**

## 3. Rejestr aktywnej sesji CarPlay

- [ ] 3.1 Moduł `project_integration/monitor/carplay_sessions.py`: `load()`, `set_active(session_id, project)`, `get_active(session_id, now)` z wygaśnięciem po 600 s, `mark_pending(session_id)`; lock przez `monitor/lockutil.py`
- [ ] 3.2 Integracja z endpointem: po parse zapis / odczyt rejestru; `X-Dispatch-Outcome: resolved` dla formy 1
- [ ] 3.3 Testy w `tests/test_carplay_sessions.py`: wygaśnięcie, `pending` po timeout, odnowienie przy użyciu formy 3
- [ ] 3.4 Smoke test z komputera: cztery sekwencyjne POST z tym samym `X-Session-Id`: (a) „projekt car integration", (b) „pokaz git status", (c) „projekt car history", (d) „co tam" — sprawdzić, że (b) idzie do car_chatgpt_integration, (d) do car_history

## 4. Odmowy i log mijanek

- [ ] 4.1 Lista słów kluczowych w `car_parser.py` (reuse jeśli istnieje w `voice_gateway`, inaczej dołożyć stałą `REFUSE_PATTERNS`); funkcja `should_refuse(text) -> (bool, matched_pattern)`
- [ ] 4.2 Zapisy odmów do `project_files/run_files/carplay_refusals.jsonl` i mijanek do `project_files/run_files/carplay_misses.jsonl` (jeden JSON na linię: `ts`, `session_id`, `transcript`, `candidates`, `pattern`); dopisywanie z lockiem na pliku
- [ ] 4.3 Testy odmowy: dla każdego wzorca z listy — jeden test; sprawdzian, że `send-keys` nie został wywołany (mock `subprocess.run`)

## 5. Token wspólny HA ↔ bramka (po D10 — zastąpiło Shortcut iOS)

- [ ] 5.1 Wygenerować wspólny token: `python -c "import secrets; print(secrets.token_hex(32))"`; zapisać w **obu** maszynach do `~/.claude/car_tokens.json` jako `{"token": "<hex>", "created": "<iso>"}`
- [ ] 5.2 Endpoint `/api/car/dispatch` czyta plik tokenów przy starcie bramki (funkcja `load_car_tokens()`); 401 gdy nagłówek `Authorization: Bearer <token>` nie pasuje
- [ ] 5.3 HA Claude: wartość tokenu w `rest_command_claude.yaml` jako `!secret car_token`, odpowiedni wpis w `secrets.yaml` na Pi
- [ ] 5.4 Dokumentacja rotacji w `notes/HANDOFF_carplay_okna.md`: jak podmienić token w obu miejscach bez przerwy > 60 s

## 6. Prerejestracja i pomiar w jeździe

- [ ] 6.1 PREREJESTRACJA (przed jazdą, ZASADY 3.3): hipoteza „≥ 7/10 udanych prób, mediana `koniec dyktowania → pierwsze słowo z głośnika` ≤ 20 s, ≥ 8/10 poprawnych transkrypcji nazwy projektu i promptu łącznie"; pytania: po jednym do trzech projektów (`Car_chatGPT_integration`, `project_integration`, `HA`), każde 3 razy, plus 1 test wygaśnięcia sesji po 11 min; definicja udanej próby = `send-keys` wykonany do właściwego projektu i `Glosowo:` dotarł audio zrozumiałym po polsku; **jedna** statystyka: mediana łącznego czasu; **liczba testowanych porównań: 1** (tylko ścieżka główna, nie porównujemy wariantów); poprawka na wielokrotność niepotrzebna; konfuzje: zasięg LTE/5G (zapis mocy sygnału przed każdą próbą), prędkość (zapis GPS), model TTS (`voice_choice.json` zamrożony); **warunek NEGATYWU**: mediana > 30 s albo udane < 5/10 ⇒ odrzucenie i powrót do design; **czego wynik NIE uprawnia**: nie mówi nic o rozmowie wieloturowej z pamięcią kontekstu, o poleceniach wymagających „yes/no" ani o jakości TTS poza polskim
- [ ] 6.2 Zasilanie peceta w pracy aktywne (`poc-carplay-command 1.7`); maszyna z tmux-ami 22 projektów nie zasnęła przez 2 h przed pomiarem (zapis `powercfg /requests`)
- [ ] 6.3 Jazda pomiarowa: ≥ 10 prób, ≥ 3 próby przy prędkości ≥ 70 km/h; tabela w `notes/HANDOFF_carplay_okna.md` z kolumnami: nr, pytanie, projekt rozpoznany, transkrypcja (OK/pomyłka), outcome (`sent`/`ambiguous`/`missing`/`refused`/`timeout`), t_dyktowanie [s], t_odpowiedz [s], prędkość [km/h], LTE/5G, uwagi
- [ ] 6.4 Opracowanie: policzyć statystyki, każdą nieudaną próbę przypisać do warstwy (Siri / Whisper / parser / resolve / send-keys / capture-pane / TTS / sieć); wpis negatywów jako negatywów (ZASADY 5.8)
- [ ] 6.5 Decyzja PoC (ZASADY 5.1): zaliczony / negatywny; wpis do HANDOFF; rekomendacja — czy iść dalej do iteracji drugiej (otwieranie okien głosem, polecenia yes/no), czy czekać

## 7. Zamknięcie zmiany

- [ ] 7.1 Usunięcie tymczasowego endpointu `/api/car/test-audio` z kroku 1.2; sprawdzian `grep -n "test-audio" project_integration/monitor/voice_gateway.py`
- [ ] 7.2 Notatka sesji wg szablonu (ZASADY 1.1) z liczbami z 6.3
- [ ] 7.3 Aktualizacja `notes/start.md` sekcja „Ostatnia sesja"
- [ ] 7.4 `python notes/gen_openspec_status.py` → commit zaktualizowanego `openspec/STATUS.md`
- [ ] 7.5 Prośba o archiwum zmiany po pomiarze: `/opsx:archive carplay-okna-projektow` (wywołuje użytkownik)
