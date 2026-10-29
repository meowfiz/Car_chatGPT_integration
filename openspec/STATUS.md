# OpenSpec task status (generated)

Generated 2026-10-29 10:06. Regenerate with `python notes/gen_openspec_status.py` after updating any change's `tasks.md`. Do not hand-edit this file.

**Overall: 91/209 tasks complete across 6 changes.**

## Summary (most recently updated first)

| Change | Status | Last updated |
|---|---|---|
| [car-dialog-okna](changes/car-dialog-okna/tasks.md) | 14/27 | 2026-10-29 |
| [carplay-okna-projektow](changes/carplay-okna-projektow/tasks.md) | 43/74 | 2026-10-13 |
| [voice-intent](changes/voice-intent/tasks.md) | 26/29 | 2026-10-05 |
| [voice-grok-front](changes/voice-grok-front/tasks.md) | 0/24 | 2026-10-05 |
| [poc-carplay-command](changes/poc-carplay-command/tasks.md) | 7/39 | 2026-10-05 |
| [ask-core-client](changes/ask-core-client/tasks.md) | 1/16 | 2026-10-05 |


---

## car-dialog-okna

`14/27` tasks complete.

### 1. Plan i kontrakt (to okno)

| Done | Task |
|---|---|
| [x] | 1.1 proposal, design (D1-D9), spec `car-dialog` - 2026-10-29 |
| [x] | 1.2 Tabela scenariuszy e2e `notes/car_dialog_scenariusze.md`: wypowiedź -> oczekiwany `outcome`/`state`/początek `text` (>= 30 wierszy, w tym graniczne z R1); to jest wspólny kontrakt dla testów huba i e2e |
| [x] | 1.3 Zlecenie okna `project_integration` (grupa 2) i okna `HA` (grupa 3) wysłane; wyslane przez send_task.py 2026-10-29 (oba OK, bridge GEIH38C), godzina w notatce sesji |

### 2. Hub: `project_integration` (okno huba)

| Done | Task |
|---|---|
| [x] | 2.1 O1: zmierzyć, czy relay drugiej maszyny zwraca odpowiedź okna (`/task` jednokierunkowy?); wynik w `notes/HANDOFF_car_dialog.md`; jeśli brak - dołożyć `GET /reply` -- zrobione: relay jednokierunkowy, odpowiedz z `/spoken` po 4,2-6,1 s, `GET /reply` zbedny (raport huba 594b9c9) |
| [x] | 2.2 `tools/car_dialog.py`: czyste `decide(state, text, world)`, parser komend (D2), wybór maszyny (D3), renderowanie krótkich komunikatów; testy jednostkowe z tabeli 1.2 -- zrobione: 35 wierszy tabeli = 35 testow |
| [x] | 2.3 Mutacje (ZASADY 4.4): wyłącz „tylko na początku zdania", zamień domyślną maszynę, pomiń pending - każda ma wywalić test -- zrobione: mutacje 11/11 decide, 8/8 kolejka, 7/7 endpoint |
| [x] | 2.4 `POST /api/car/say` w `voice_gateway.py`: odmowa -> dialog -> akcja; stare `/api/car/*` bez zmian jako aliasy -- zrobione, pole opcjonalne `zrodlo` |
| [x] | 2.5 Kolejka FIFO per `(maszyna, projekt)` z dziennikiem i odtworzeniem po restarcie; test restartu -- zrobione (`tools/car_queue.py`) |
| [x] | 2.6 Odpowiedź asynchroniczna przez `script.odpowiedz_asystenta` dla `queued` -- zbudowane i testowane atrapami; odtwarzanie w aucie czeka na HA 3.4 |
| [x] | 2.7 `car_trail.jsonl`, streszczenie okna do `voice_history` przy „wróć", „gdzie jestem" z `/api/state` + `is_busy` -- zrobione |
| [x] | 2.8 Adapter `RemoteRelay` (po 2.1); okno zamknięte -> `okna.py`, czekanie na gotowość -- zrobione, zywo sprawdzone; otwieranie zamknietego okna tylko atrapami |
| [ ] | 2.9 Wykrywanie monitu o zgodę w panelu okna -> komunikat „okno czeka na zgodę" (D8) -- CZESCIOWO: tylko okna na tej maszynie (z domu nie widac panelu) |
| [ ] | 2.10 ZASADY 2.14: wersja bramki i klon sprawdzone na **obu** maszynach, pomiar z dwóch urządzeń naraz -- CZESCIOWO: praca aktualna; dom ma bramke 286e620e52fe bez /api/car/say, potrzebny `start` + restart voice; test z dwoch urzadzen niezrobiony |
| [x] | 2.11 NAPRAWIONE (hub, bramka praca 2e870112f65c: wersja stanu, spozniony zapis nie zmienia pozycji; e2e --live lancuch 7 PASS, 0 FAIL). BLAD z e2e 2026-10-29: `przejdz do Car` -> `wroc` -> `gdzie jestem` zwraca okno zamiast rozmowy glownej (mode=window); test sekwencyjny + mutacja; zlecone oknu huba |
| [x] | 2.12 Poprawki huba ce8af05 (bramka praca 8a60332e0312): polecenie z nazwa okna w rozmowie glownej przechodzi i wysyla cale zdanie; rozmyte nazwy STT (WESSA/WESTA -> vESSA); do okna idzie `[glos-auto]`; stan nie resetuje sie przez stara sciezke dispatch. e2e: 24 PASS, 1 FAIL (wiersz 6, dom offline), 18 SKIP. Wiersze 36-38 tabeli sa z tej poprawki |

### 3. HA: okno `HA`

| Done | Task |
|---|---|
| [ ] | 3.1 O2: zbadać zastępczego agenta konwersacji (bez słowa „Claude"); wynik zapisany |
| [ ] | 3.2 Intent `ClaudeSay` (`claude {pytanie}` + warianty) -> `rest_command.car_say` z `session_id = conversation_id`, `text = pytanie`; odpowiedź = pole `text` |
| [ ] | 3.3 Stare intenty (Dispatch/Status/Podsumowanie/Otworz/Zamknij/Powtorz) przekierowane na `car_say` z odpowiednim tekstem albo usunięte; `PomocClaude` zaktualizowana o nowe komendy |
| [ ] | 3.4 Odpowiedź asynchroniczna: `script.odpowiedz_asystenta` przyjmuje wywołanie z bramki dla satelity rozmowy auta |
| [ ] | 3.5 Deploy `ssh ha-tailscale` + reload, test fraz z tabeli 1.2 przez `conversation.process` |

### 2a. Dom i integracja (po raporcie huba 2026-10-29)

| Done | Task |
|---|---|
| [ ] | 2a.1 Dom (DESKTOP-FFSHIOA): `start` + restart `voice` (`monitor/services.py --restart --only voice`), potem `X-Gateway-Version` zgodny z praca (ZASADY 2.14); wykonuje uzytkownik lub okno huba na domu |
| [ ] | 2a.2 Test z dwoch urzadzen naraz (telefon + auto/komputer, ten sam projekt): kolejka okna wspolna, stany per `session_id` rozdzielne |
| [ ] | 2a.3 Dialog z oknem HA wymaga atrapy: tabela zaklada HA otwarte na obu maszynach, a e2e wpisalo `drugi` do prawdziwego okna HA (blad z raportu). Runner e2e nie wysyla tresci do okien bez `--live` (patrz 4.1) |

### 4. E2E i pomiar (to okno)

| Done | Task |
|---|---|
| [x] | 4.1 (runner gotowy, bez `--live` nie wysyla tresci do prawdziwych okien: `poc/car_dialog_e2e.py`, 5 testów w `test_car_dialog_e2e.py`; na `/api/car/say` jeszcze nieuruchomiony - endpoint nie istnieje, 2026-10-29 połączenie odrzucone). Rozszerzyć `tools/voice_e2e.py` (hub) albo dołożyć `poc/car_dialog_e2e.py` (tu): przebieg „jakie projekty pracują -> przejdź do X -> 3 polecenia -> gdzie jestem -> wróć -> pytanie główne" na prawdziwej ścieżce HA -> bramka -> okno |
| [ ] | 4.2 PREREJESTRACJA przed pomiarem w aucie (ZASADY 3.3): hipoteza „>= 9/10 przejść do okna kończy się poprawnym projektem i maszyną bez dotykania telefonu", jedna statystyka, warunek NEGATYWU (< 7/10 -> wracamy do gramatyki D2, bez dostrajania po wyniku), czego wynik nie uprawnia (nie mierzy jakości odpowiedzi okna) |
| [ ] | 4.3 Pomiar w aucie (>= 10 przejść, >= 10 poleceń w oknie, 3 „gdzie jestem", 3 powroty), tabela w `notes/HANDOFF_car_dialog.md` |
| [ ] | 4.4 Notatka sesji, `python notes/gen_openspec_status.py`, commit i push (ZASADY 2.10) |

## carplay-okna-projektow

`43/74` tasks complete.

### 1. PoC gating — Siri Shortcut odtwarza audio z HTTPS tailnetu w CarPlay

| Done | Task |
|---|---|
| [x] | 1.1 Jednorazowy skrót iOS „CarPlay audio test": `GET` endpoint `/api/car/test-audio` (zwraca `audio/mpeg` edge-tts z „test glosu w aucie"), `Get Contents of URL`, `Play Sound`. Instrukcja krok po kroku w `notes/HANDOFF_carplay_okna.md` (sekcja 1.1) |
| [x] | 1.2 Tymczasowy endpoint `/api/car/test-audio` w `project_integration/tools/voice_gateway.py` (nie `monitor/` — tam go nie ma; `pack/` dostanie go dopiero po PoC); edge-tts generuje audio on-demand (`speak_edge(CAR_TEST_TEXT)`), żadnego trzymania pliku w repo. Bind dziedziczony z bramki (tailnet-only przez `discover_tls()`), bez tokenu w PoC, oznaczony `# TODO: usunac po PoC` |
| [ ] | 1.3 Pomiar na postoju: 3 próby „Hey Siri, CarPlay audio test" z telefonu z CarPlay podpiętym po USB; zapis do HANDOFF kolumn: nr, start, odtworzone (tak/nie), opóźnienie [s], jakość (zrozumiałe/zniekształcone), uwagi |
| [x] | 1.4 Decyzja PoC (2026-10-12): **Skrót A urywa** (user słyszał „test" zamiast „test głosu w aucie"), **Skrót B dociąga** ale głos systemowy Siri. Zapis w HANDOFF jako „ograniczenie techniczne CarPlay" (ZASADY 5.8). **Nowa decyzja** (D10 w design.md): porzucamy Siri Shortcut jako wejście, przełączamy na HA Assist w CarPlay. Grupa 2 (`/api/car/command`) **PORZUCONA**, zastępuje ją nowa grupa 1.5 (HA Assist) i przerobiona grupa 2 (`/api/car/dispatch`). |

### 1.5 Przełączenie wejścia na HA Assist w CarPlay (2026-10-12, po D10)

| Done | Task |
|---|---|
| [x] | 1.5.1 HA Claude w oknie `HA`: dodać kafelek **Assist** jako Quick Access w CarPlay (HA Companion → ustawienia → CarPlay), zweryfikować lokalny pipeline PL + VCC głos Sznuka — potwierdzone w kuchni, pełne zdanie bez cięć |
| [x] | 1.5.2 Rozszerzenie `voice/claude_sentences_pl.yaml` o intent `DispatchClaude` z frazami: „Claude do okna {pytanie}", „Claude w oknie {pytanie}", „Claude otwórz okno {pytanie}", „Claude kontynuuj {pytanie}", „Claude dalej {pytanie}". Wildcard na całość (po stronie bramki `parse_car_prompt` wyciąga nazwę projektu i resztę) |
| [x] | 1.5.3 **Nieaktualne** — aliasy zrobione w `parse_car_prompt` przez wywołanie `okna.resolve` (fuzzy exact→prefix→substring), bez osobnego pliku. `monitor_repos.env` jest jedynym źródłem prawdy. Pominięte świadomie |
| [x] | 1.5.4 `voice/rest_command_claude.yaml` — nowy wpis `claude_dispatch` POST do `/api/car/dispatch` z `Authorization: !secret car_token_header`, body `{session_id (= conversation_id), project: "", prompt: pytanie}`. Czeka na HA stronę: wklejenie secretu i reload |
| [ ] | 1.5.5 Seria C pomiarowa w aucie (3 próby „test głosu w aucie" przez kafelek Assist w CarPlay) — tabela w `HANDOFF_carplay_okna.md`. **Jedyny PoC-gating dla reszty zmiany po D10:** < 2/3 pełnego dociągu → wracamy do design, dalsze grupy nie rozpoczynają się |
| [ ] | 1.5.6 Dla PoC seria C **wystarczy fraza stała HA** („test głosu w aucie" → TTS „test głosu w aucie") — nie potrzebujemy jeszcze pełnego dyspozytora z 1.5.2–1.5.4; te dochodzą po zdaniu bramki |

### 2. Endpoint `/api/car/dispatch` w bramce (zastępuje stary `/api/car/command` po D10)

| Done | Task |
|---|---|
| [x] | 2.1 Szkielet endpointu `POST /api/car/dispatch` w `project_integration/tools/voice_gateway.py`: JSON `{session_id, project, prompt}`, Bearer token z `~/.claude/car_tokens.json`, odpowiedź JSON `{text, outcome, resolved_project?}`. Smoke test z pecetu 2026-10-12: `project_integration` 5.2 s, fuzzy `project integration` 6.5 s, sticky session reuse 5.3 s, timeout obsłużony |
| [x] | 2.2 Parser `parse_car_prompt(prompt, resolve_fn)` w bramce (nie w HA — HA wysyła całość jako wildcard `{pytanie}`, bo Speech-to-Phrase nie zna nazw projektów). Rozpoznaje: `kontynuuj X` → mode=continue, `<1-3 slow nazwa> <reszta>` → dispatch, sama nazwa → set_only, nic → fallback do sticky. 8 testów jednostkowych |
| [x] | 2.3 Resolve nazwy projektu wywołuje `okna.resolve` jako sanity check aliasu z HA; `missing`/`ambiguous` zwrot w JSON. Smoke: `panda` → `missing` (0.03 s), `rib` → `RibnXtr2026` (single match) |
| [x] | 2.4 Transport do pane: **reuse `cli_bridge.type_into`** (load-buffer + paste-buffer + Enter, polskie znaki bez kodowania przez CLI). Zero duplikacji — ta sama funkcja, co dispatch worker |
| [x] | 2.5 Zwrot `Glosowo:` z pane: pętla `cli_bridge.capture` + `extract_reply` + `spoken_lines` co 500 ms, do pierwszej linii nowszej niż `before` lub timeout 30 s. Reuse z `cli_bridge` |
| [x] | 2.6 Pole `text` w JSONie = pierwsza linia `Glosowo:` **bez prefiksu** (robi `spoken_lines`), outcome `sent`/`timeout`/`missing`/`ambiguous`/`refused` |
| [x] | 2.7 Testy jednostkowe `project_integration/tools/tests/test_car_dispatch.py`: 26 passed + 1 świadomy skip. Pokrywa: `should_refuse_car` 11 wzorców + 2 normalizacje spacji, `car_sessions_*` set/get/expire/overwrite, `load_car_tokens` BOM UTF-8/rotacja/short/malformed/missing |
| [x] | 2.8 Smoke test integracyjny z pecetu: 4 przypadki OK: `missing` (0.03 s), `refused` (0.02 s), `no token` → 401, dispatch do `project_integration` sticky session (5.2–6.5 s) |

### 2a. Rozszerzone endpointy funkcjonalne (sprint 2026-10-12)

| Done | Task |
|---|---|
| [x] | 2a.1 `GET /api/car/status` — agreguje `/api/state`, zwraca Głosowo tekst z liczbami. Smoke: 22 projekty, 182 zadania otwarte, 1 niewypchnięty, 3 pracujące |
| [x] | 2a.2 `POST /api/car/open` body `{project}` — subprocess do `tools/okno.py`, idempotentne, zwraca „otwieram X" lub „okno X juz dziala". Smoke: `voice` otwarte w 5.5 s |
| [x] | 2a.3 `GET /api/car/project/<name>/summary` — fuzzy przez `okna.resolve`, agreguje rekord z `/api/state`. Smoke: `car integration` → `Car_chatGPT_integration`, `HA` → stan 2 z 19 otwartych |
| [x] | 2a.4 **4-ty tier w `okna.resolve`: token-match** — gdy query ma ≥ 2 słowa, dopasowanie jeśli każdy token jest podciągiem znormalizowanej nazwy. Potrzebne dla „car integration" vs `Car_chatGPT_integration`. 4 nowe testy przeszły, cała suita 74/75 |

### 2b. Rozszerzenia głosowe (sprint 2026-10-12 wieczór)

| Done | Task |
|---|---|
| [x] | 2b.1 `POST /api/car/todo` body `{text, project?, session_id?}` — zapisuje TODO głosem do `~/.claude/carplay_todos.jsonl`. Project z sticky jeśli puste. 3 scenariusze smoke |
| [x] | 2b.2 `POST /api/car/zamknij` body `{session_id}` — kasuje sticky, zwraca „zamkniete bylo X" lub „nie bylo aktywnej sesji" |
| [x] | 2b.3 `POST /api/car/powtorz` body `{session_id}` — powtarza ostatnie Glosowo. Rejestr sesji trzyma `last_text`, dispatch aktualizuje |
| [x] | 2b.4 Pure helpery: `build_car_status_text`, `build_car_project_text`, `car_update_last_text`, `car_get_last_text`. 9 nowych testów (razem 47 passed, 1 skipped) |
| [x] | 2b.5 Dokumentacja: `notes/HANDOFF_car_endpoints.md` (337 linii) — kontrakt, autoryzacja, rejestr sesji, odmowy, 4-tier resolver, wzorzec rest_command dla HA |

### 2c. Dojrzałość PoC (sprint 2026-10-12 noc)

| Done | Task |
|---|---|
| [x] | 2c.1 `GET /api/car/ostatnie_todo?n=5` — recytacja ostatnich N TODO z `carplay_todos.jsonl`; `?n=` od 1 do 10 |
| [x] | 2c.2 `poc/car_selftest.py` — sanity check 11 endpointów, PASS/FAIL/czas, bez body check. Smoke 11/11 w ~42 s |
| [x] | 2c.3 Code review subagent (0 BLOCKER, 4 NICE-TO-HAVE, 2 COSMETIC): auth helper dedup (`_car_authorized`), rozszerzone `CAR_REFUSE_PATTERNS` z 11 do 23 wzorców (powershell/iex/\|sh/del /s/chmod 777/dd/mkfs/rm -fr/rm --recursive) + 12 nowych testów |
| [x] | 2c.4 Fix N1 race w rejestrze sesji: `threading.Lock` wokół RMW sekwencji w `car_set_active`, `car_update_last_text`, `_car_zamknij`. Test: 20 wątków set_active → 20 session_id w rejestrze. Lazy path lookup w `car_sessions_{load,save}` (default=None, re-read z CAR_SESSION_PATH) |
| [x] | 2c.5 Spec rozszerzony o 2 nowe wymagania: endpointy wsparcia (todo/zamknij/powtorz/ostatnie_todo) i 4-tier `okna.resolve` |
| [x] | 2c.6 `GET /api/car/projekty?n=7` — dynamiczna lista nazw projektów do wymówienia dla PomocClaude (zamiast hardcoded). Smoke: pierwsze 5 OK |
| [x] | 2c.7 `GET /api/car/metryki?h=24` — parser `voice_gateway.log`, zlicza `car-*` wpisy. Smoke: 121 wywolan w 24h, top 3: dispatch 32, poc 30, status 13 |
| [x] | 2c.8 Self-test rozszerzony do 15 endpointow (bylo 11): + projekty, ostatnie_todo, zamknij.pusty, powtorz.pusta. 15/15 PASS w ~38s |
| [x] | 2c.9 `POST /api/car/stop` body `{pane}` — awaryjne przerwanie dispatcha z auta. `tmux send-keys C-c` do pane. Z23 w pętli profesor-student. Pomiar: 347 ms (próg 2000 ms). 1 pytest nazywający porażkę („stop bez pane zwraca 400, nie 500"), self-test rozszerzony do 17/17 (+ car.stop.brak_pane 400, + car.stop.nieistniejacy 404) |
| [ ] | 2c.10 **PREREJESTRACJA Z24** (przed uruchomieniem skryptu, ZASADY 3.3): pomiar e2e `/api/car/stop` 10 prób z pecetu przez adres tailnetowy (symulacja telefonu bo user offline). **Hipoteza negatywna**: mediana > 3000 ms lub ≥ 1 timeout/5xx w 10 → endpoint nie nadaje się do auta, wracamy do architektury. **Hipoteza pozytywna**: mediana ≤ 1500 ms, p90 ≤ 2500 ms, 10/10 OK. **3 miary**: (1) latencja e2e per próba z zegarem bramki — min/median/p90/max; (2) skuteczność `tmux send-keys`: `capture-pane` przed/po, zmiana ostatniej linii = sukces, próg 10/10; (3) status HTTP: 10×200, zero 4xx/5xx, próg 10/10. **Liczba porównań: 1** (ścieżka główna /stop, bez wariantów). Konfuzje: sieć tailnet (symulacja ≠ telefon LTE), pane bez aktywnego procesu (symulowany sleep ≠ Claude Code). Wynik NIE uprawnia do: „działa pod obciążeniem" (10 prób, nie 1000), „na każdym pane" (1 pane, nie 22), „sieć LTE OK" (symulacja z pecetu). |
| [x] | 2c.10 PREREJESTRACJA Z24 commitowana przed pomiarem 23:34 UTC |
| [x] | 2c.11 Z24 pomiar: `poc/stop_e2e_pomiar.py` 10 prób, zapis `project_files/run_files/stop_e2e_2026-10-12-233411.jsonl`. Wynik: **ZALICZONE 3/3 miar**. Miara 1: min 298.2 / median 309.5 / p90 325.4 / max 326.2 ms (progi 1500/2500). Miara 2: 10/10 `send-keys` skuteczne (capture-pane zmiana). Miara 3: 10/10 HTTP 200. Wynik NIE uprawnia do: obciążenia (10 prób, nie 1000), każdego pane (1 pane), LTE OK (symulacja z pecetu — ta sama sieć co bramka) |
| [x] | 2c.12 **PREREJESTRACJA Z25** w commit 4f5e54f (przed mutacją). ZASADY 3.3 zachowane |
| [x] | 2c.13 Z25 wynik: **NEGATYW hipotezy** (ZASADY 5.8). Pytest `test_stop_bez_pane_zwraca_400_nie_500` **przeszedł mimo mutacji** `rc == 0` → `rc != 0`. Przyczyna: test pokrywa branch `brak pane → 400` (pre-send-keys), mutacja jest post-send-keys. **ALE** integration test (self-test live) **złapał mutację** — zwrócił `outcome="timeout"` zamiast `"sent"`. Wniosek: ZASADY 4.4 „testy sprawdzone mutacją" spełnione dla self-testu live, **nie dla pytest**. Pytest nie pokrywa sukces-branche semantyki `send-keys`. Kod przywrócony, `git diff` pusty (zweryfikowane) |
| [ ] | **WYMAGA PROJEKTU — nie fix in-place** (KRYT 1 z code review 2 Z25): semantyka `/api/car/stop` dla sesji wielo-okiennych i `claude -p` signal handler. `send-keys -t =session:` idzie do aktywnego pane, nie konkretnego. `claude -p` ma własny signal handler — pojedyncze C-c czyści prompt, nie zabija generowania. Text „stopnieto X" kłamie. Decyzja projektowa (nowy proposal/design, nie bugfix). Zapisane w `notes/HANDOFF_voice_gateway.md` |
| [x] | 2c.14 **Z26 FIX KRYT 2**: `_car_stop` miał `outcome="timeout"` dla `rc != 0` bez TimeoutExpired. Fix 2026-10-13 noc: osobny `except subprocess.TimeoutExpired` → `outcome="timeout"` 200 OK; `rc != 0` bez timeoutu → `outcome="error"` 200 OK + pole `rc`. Spec rozszerzony: enum `sent\|resolved\|ambiguous\|missing\|refused\|error\|timeout`. **Mutation test** (ZASADY 4.4 druga połowa): nowy pytest `test_stop_rc_nonzero_zwraca_outcome_error_nie_timeout` używający `monkeypatch` dla `subprocess.run` z `rc=1`. Mutation: zamiana `"error"` → `"timeout"` → test PADŁ (`E - error / E + timeout`), kod przywrócony. **99 pytest passed** (było 98, +1) |
| [x] | 2c.15 **PREREJESTRACJA Z27** w commit przed kodem. ZASADY 3.3 zachowane |
| [x] | 2c.16 **Z27 FIX**: `POST /api/car/rotate_token` zbudowany. `secrets.token_hex(32)` → nowy token, zapis atomowy `tmp + os.replace`, odpowiedź JSON `{token, rotated_at, token_hash (sha256[:8])}`. **Nie loguje tokena**, tylko `rotated_at` i hash prefix. **Odczyt per-request z dysku** (bez cache w pamięci — rotacja działa bez restartu). **2 pytesty**: integracyjny (3 asercje: stary→401, nowy→200, plik zmieniony przez `_car_rotate_token` na FakeHandler) + atomowości (symulacja wyjątku przed `os.replace` → stary token dalej w pliku). **Mutation**: `os.replace` usunięty → test padł z `assert nowy in nowe_tokeny` (nowy token nie w pliku). Kod przywrócony. **Live test**: rotacja z backupem — ROTACJA OK (hash 05e2b7db), stary→401, nowy→200, backup przywrócony dla HA. **Fix uboczny**: `load_car_tokens(path=None)` lazy lookup (było `path=CAR_TOKEN_PATH` — monkeypatch nie działał, odkryte przez test). **101 pytest** (było 99, +2), self-test 17/17 |
| [ ] | 2c.17 **PREREJESTRACJA Z28** (przed implementacją, ZASADY 3.3): wrapper `_resolve_window_with_aliases(query)` używa aliasów z Orchestratora (`GET /api/projects`, cache TTL 600 s, HTTP timeout 2 s, 5xx/timeout → fallback do starego cache lub `okna.resolve` solo, 4xx → log + wyjątek do góry — bo to konfig błąd, nie cichy fallback). **Hipoteza**: redukuje do zera odsetek `project=None` dla fraz z `poc/aliases.json`, bez zmiany zachowania dla fraz spoza aliases. **Dane testu**: - **Zbiór A (39 par)**: 3 frazy × 13 projektów z `poc/aliases.json` (fraza → kanon) - **Zbiór B (10 literalnych fraz, zadeklarowanych PRZED implementacją — nie generowane dynamicznie)**: 1. `jakis losowy projekt` 2. `cos czego nie ma` 3. `panda` 4. `prosze o pomoc` 5. `co teraz` 6. `kot domowy` 7. `programowanie w rust` 8. `wczoraj spadal snieg` 9. `nic takiego` 10. `siedem dziewiec` - **Statystyka**: M1 = ile z 39 par rozwiązuje się do kanonicznej (próg **39/39**); M2 = ile z 10 fraz zbioru B zachowuje puste zwroty (próg **10/10**) - **Kontrola odtworzenia P2 (ZASADY 5.3)**: skrypt pomiarowy **odmawia uruchomienia** gdy wrapper z pustym cache aliasów nie zwraca identycznych wyników co `okna.resolve` solo dla wszystkich 49 fraz (A ∪ B) - **Liczba porównań**: 1 (wrapper vs status quo) - **Warunek NEGATYWU**: M1 < 39/39 albo M2 < 10/10 → przerywam, nie stroję do magic konstanty - **Wynik NIE uprawnia**: do „fuzzy ogólnie lepszy"; do opinii o rzeczywistych frazach z auta (tylko syntetyczne); do frontu HA Assist ani Siri; do opinii o aliasach wielokomponentowych w kanonie |
| [x] | 2c.18 **Z28 WYNIK** (noc 2026-10-13, po PREREJESTRACJI 2c.17): wrapper `_resolve_window_with_aliases` zbudowany. **Kontrola odtworzenia P2**: wrapper z pustym cache == `okna.resolve` solo dla **49/49 fraz** (ZASADY 5.3 spełniona). **Pomiar główny**: **M1 = 42/42** (nie 39 — `aliases.json` ma 14 projektów, nie 13 jak policzyłem w prerejestracji; wszystkie rozwiązują się do kanonu); **M2 = 10/10** (wszystkie frazy zbioru B zachowują puste zwroty). **DECYZJA: ZALICZONE**. 4 nowe pytesty (`test_wrapper_aliasow_*`: mapuje, fallback, pusty cache, 4xx), **68 pytest passed** (było 64, +4). Skrypt pomiarowy `poc/z28_aliases_pomiar.py` z kontrolą P2 odmawiającą uruchomienia głównego pomiaru przy rozjazdach. **Fix ubocznego nie było** — kod przeszedł od razu. **Wrapper nie podpięty do `_car_dispatch`** w tej iteracji — osobna tura po pomiarze z rzeczywistymi frazami z auta (ZASADY 3.1: osobna zmiana) |
| [ ] | 2c.19 **PREREJESTRACJA Z29a** (PRZED mutacjami, ZASADY 3.3 + 4.4): mutation test wrappera `_resolve_window_with_aliases`. **Hipoteza**: każdy z 4 testów `test_wrapper_aliasow_*` wykryje co najmniej 1 mutację swojej gałęzi. **Lista 4 mutacji** (ZASADY 5.4 — dokładnie 4, nie więcej): 1. **Wyłącz mapowanie**: w `_resolve_window_with_aliases` zwróć od razu `resolver_fn(query)` z pominięciem cache aliasów → ma paść `test_wrapper_aliasow_mapuje_fraze_do_kanonu` 2. **Zepsuj fallback**: dla frazy spoza aliasów zwróć `[]` zamiast `resolver_fn(query)` → ma paść `test_wrapper_aliasow_fallback_do_resolver_dla_fraz_spoza` 3. **Zepsuj zachowanie pustego cache**: przy pustym cache zwróć `[]` zamiast delegować do resolver → ma paść `test_wrapper_aliasow_pusty_cache_zachowuje_sie_jak_resolver_solo` 4. **Zepsuj politykę 4xx**: dla 4xx w `_car_cached_aliases` zignoruj zamiast podnieść (cichy fallback) → ma paść `test_wrapper_aliasow_4xx_rzuca_wyjatek_do_gory` **Statystyka**: liczba mutacji wykrytych / 4. **Próg = 4/4**. **Warunek NEGATYWU** (ZASADY 5.8): < 4/4 → mutacja niewykryta dostaje własny test; stop dalszych mutacji. **Wynik NIE uprawnia**: do kompletnego pokrycia semantycznego wrappera. 4 mutacje = 4 gałęzie, nie wszystkie |
| [x] | 2c.21 **Z29c-fix NICE #4** (2026-10-13 noc, po pomiarze git log aliases.json przez profesora): asercja `log.call_count` dodana w `test_wrapper_aliasow_4xx_rzuca_wyjatek_do_gory` — monkeypatch na `vg.log` zlicza wpisy `car-aliases` z komunikatem o 4xx. **Mutacja ręczna**: usunięcie `log("car-aliases", ...)` dla 4xx → test padł z `assert False` (anyany log z komunikatem 4xx w zbiorze). Kod przywrócony, `git diff` pusty. **ZASADY 4.4 druga połowa** spełniona dla loga 4xx: mutacja `log → pass` nie przeszłaby. Pytest: 69 → 69 passed (bez regresji, test rozszerzony) |
| [ ] | 2c.22 **Z29c NICE #5** — TTL 600 s w cache aliasów. **Potencjał**: user edytuje `aliases.json` → `sync_aliases.py` → Orchestrator, do 10 min opóźnienia zanim bramka zobaczy („zmieniłem i nie działa"). **Kryterium akceptacji**: albo (a) endpoint `POST /api/aliases/invalidate` wymuszający re-fetch, albo (b) ETag/If-None-Match w `GET /api/projects` z invalidacją po zmianie. **WYMAGA POMIARU PRZED IMPLEMENTACJĄ** (ZASADY 5.10 — jedna zadeklarowana reguła, nie tuning per przypadek): ile razy w typowej sesji auta user zmienia alias? Jaki jest realny TTL potrzebny? Bez tego fix jest tuningiem bez miary — osobna prerejestracja. **DANE BAZOWE pomiar 1/2 (git log 2026-10-13 noc, profesor)**: 11 commitów w `poc/aliases.json` od 2026-09-16 do 2026-10-07, 8 unikalnych dni, okno 21 dni. **Mediana odstępu 2 dni, max 6 dni**. TTL 600 s pokrywa **0,35%** cyklu typowej zmiany (10 min / mediana 2880 min). Niespójność cache w aucie trwa max 10 min po edycji. Odpowiada na pytanie „jak często TTL wygasa między edycjami", ale nie „ile zapytań trafia w okno nieświeżości". **PREREJESTRACJA pomiar 2/2 (2026-10-13 noc, przed analizą)**: częstość wywołań `_car_cached_aliases` z `voice_gateway.log`. - **Jednostka**: wywołań `_car_cached_aliases` / dobę — **mediana po dniach z wywołaniami > 0** (zera z nocy rozwadniają średnią; wg profesora). - **Podział** (zgodnie z instrukcją): osobno (a) całkowita liczba wywołań, (b) hit cache (TTL nie wygasł), (c) resolver_fn (TTL wygasł, odświeżenie); interesuje nas **(b)** jako zapytania zwracające potencjalnie stare dane. - **Próg decyzyjny**: < 10 /dobę = non-issue potwierdzony; 10–100 = raport; > 100 = NICE #5 awansuje do „do rozwiązania". - **Warunek NEGATYWU**: jeśli log nie zawiera osobnych wpisów dla hit vs resolver_fn, zapisujemy to wprost (ZASADY 5.8) i nie szacujemy przez proporcje. - **Czego wynik NIE uprawnia**: do decyzji o implementacji invalidacji na edycji (osobna prerejestracja z metodą i progiem akceptacji); do „NICE #5 zamknięty" nawet przy < 10/dobę — zamyka go dopiero zapis w notatce „decyzja: zostawiamy, warunek powrotu: Z". - **Pochodzenie (ZASADY 6.1)**: nagłówek pomiaru = commit + SHA-256 pliku logu + zakres dat + dokładna komenda filtrująca. **POMIAR 2/2 WYNIK (2026-10-13 noc, po prerejestracji w commit ba4472e)**: - **Nagłówek pochodzenia**: `voice_gateway.log` SHA-256 `062ec4420e6b6eae1cb9a4b0fa252452317363c859c89bd2a94df9a1d7aea3ce`, zakres `2026-09-18T07:42 → 2026-10-12T22:36`, komenda `grep -c "car-aliases"` = **52 wpisów**. - **PODWÓJNY NEGATYW (ZASADY 5.8)**: 1. **Log NIE rozróżnia hit cache vs resolver_fn** — wszystkie 52 wpisy to `fetch failed (ConnectionError) -- fallback do stare`. Ścieżka sukcesu (cache miss → ok fetch) nie zostawia śladu, hit cache (TTL nie wygasł) też nie. Nie szacujemy przez proporcje (zgodnie z warunkiem negatywu). 2. **Wszystkie 52 wpisy pochodzą z 2026-10-12 wieczór — mojego własnego pomiaru Z28/Z29**. Wrapper nie jest podpięty do `_car_dispatch` w produkcji (iteracja 1 Z28, świadome). Zerowe wywołania z realnego ruchu z telefonu/HA. - **DECYZJA**: NICE #5 **pozostaje nie-priorytetem**, ale z innego powodu niż pomiar 1/2 sugerował. Nie dlatego że „0,35% cyklu to szum" (to był pomiar 1/2), ale dlatego że **wrapper nie ma jeszcze żadnych rzeczywistych wywołań** — do czasu podpięcia pod `_car_dispatch` + przynajmniej 2 tygodnie ruchu z auta/HA pytanie o TTL jest przedwczesne. - **Warunek powrotu do NICE #5**: podpięcie wrappera do `_car_dispatch` (iteracja 2 po pomiarze serii C w aucie) + log rozróżniający hit vs resolver_fn (dodać `log("car-aliases", "hit cache q=%s" % q)` i `log("car-aliases", "resolver_fn q=%s" % q)` w `_resolve_window_with_aliases`) + 14 dni ruchu + powtórzyć pomiar 2/2. Dopiero wtedy liczba jest interpretowalna wobec progu < 10/dobę. |
| [ ] | 2c.23 **PREREJESTRACJA implementacji NICE #5** (dla przyszłej sesji, po powrocie do NICE #5 wg warunku w 2c.22): wariant decyzyjny implementacji po dopełnieniu warunku powrotu (podpięcie + log rozróżniający + 14 dni ruchu + powtórzony pomiar 2/2 > progu). - **Hipoteza**: endpoint `POST /api/car/aliases/invalidate` z Bearer tokenem wywołany po `sync_aliases.py --push` eliminuje okno niespójności cache dla 100% zapytań po edycji (max latencja: 1 trafienie HTTP localhost ≤ 400 ms wg Z24 p90). - **Dane testu** (po implementacji, osobny pomiar): - **Zbiór**: 10 symulowanych edycji aliasów przez `sync_aliases.py` (kazda inna fraza → inny alias → ta sama nazwa projektu). Po każdej edycji 1 zapytanie `_car_cached_aliases` w ciągu 1 s. - **Statystyka**: ile z 10 zapytań zwraca **nowy** alias (po edycji, przed `invalidate`), ile **nowy** (po `invalidate`). Próg: ≥ 9/10 nowych po `invalidate`, ≤ 1/10 bez `invalidate` (bo pierwsze zapytanie w 10 min oknie jeszcze trafia w cache z poprzedniej sesji). - **Alternatywa (odrzucona na starcie)**: ETag/If-None-Match w `GET /api/projects` — wymaga zmiany Orchestratora (`project_integration/server/app.py`), zwiększa zakres o drugi serwer; **invalidate endpoint** jest **lokalny** w bramce i nie wymaga ingerencji w inne komponenty. ZASADY 4.9 — mniej semantyki, o którą nikt nie prosi. - **Warunek NEGATYWU** (ZASADY 3.3): jeśli `_car_cached_aliases` zostaje przy 100% hit cache nawet po `invalidate` → implementacja ma błąd (prawdopodobnie TTL check nie resetuje się), przerywam i wrapper wraca do poprzedniej wersji; nie strojam. - **Czego wynik NIE uprawnia**: nie uprawnia do opinii o skalowalności (10 edycji ≠ 10 000); nie bada wyścigu dwóch równoległych `invalidate`; nie uprawnia do automatycznej invalidacji przy każdym PUT w Orchestratorze (to wymaga webhook, osobne zadanie). - **Pochodzenie**: ten wpis commit `TBD-przyszłej-sesji` jako prerejestracja; pomiar faktyczny z nagłówkiem (commit + SHA-256 pliku logu + zakres + komenda). |
| [ ] | 2c.24 **PREREJESTRACJA iteracji 2 wrappera** (podpięcie `_resolve_window_with_aliases` do `_car_dispatch`): warunkowa wobec pomiaru serii C PoC w aucie (grupa 6 w tasks.md). Hipoteza, próg, warunek NEGATYWU zapisane w osobnej turze po pomiarze serii C — bez niego nie wiemy, czy dyspatch głosowy w ogóle działa z realnymi frazami. Nie planujemy teraz, bo seria C jest `blocked` na user offline. |
| [x] | 2c.20 **Z29a WYNIK** (noc 2026-10-13): **4/4 mutacji wykrytych**, próg spełniony. - M1 (wyłącz mapowanie) → `test_wrapper_aliasow_mapuje_fraze_do_kanonu` **FAILED** - M2 (zepsuj fallback) → `test_wrapper_aliasow_fallback_do_resolver_dla_fraz_spoza` **FAILED** - M3 (pusty cache zwraca []) → `test_wrapper_aliasow_pusty_cache_zachowuje_sie_jak_resolver_solo` **FAILED** - M4 (cichy fallback dla 4xx) → `test_wrapper_aliasow_4xx_rzuca_wyjatek_do_gory` **FAILED** Kod przywrócony po każdej mutacji, finalny `git diff tools/voice_gateway.py` pusty, 68 pytest zielony. Mutacje nie commitowane (byłyby złamaniem produkcyjnego kontraktu). **DECYZJA: Z29a ZALICZONE 4/4** |

### 3. Rejestr aktywnej sesji CarPlay

| Done | Task |
|---|---|
| [ ] | 3.1 Moduł `project_integration/monitor/carplay_sessions.py`: `load()`, `set_active(session_id, project)`, `get_active(session_id, now)` z wygaśnięciem po 600 s, `mark_pending(session_id)`; lock przez `monitor/lockutil.py` |
| [ ] | 3.2 Integracja z endpointem: po parse zapis / odczyt rejestru; `X-Dispatch-Outcome: resolved` dla formy 1 |
| [ ] | 3.3 Testy w `tests/test_carplay_sessions.py`: wygaśnięcie, `pending` po timeout, odnowienie przy użyciu formy 3 |
| [ ] | 3.4 Smoke test z komputera: cztery sekwencyjne POST z tym samym `X-Session-Id`: (a) „projekt car integration", (b) „pokaz git status", (c) „projekt car history", (d) „co tam" — sprawdzić, że (b) idzie do car_chatgpt_integration, (d) do car_history |

### 4. Odmowy i log mijanek

| Done | Task |
|---|---|
| [ ] | 4.1 Lista słów kluczowych w `car_parser.py` (reuse jeśli istnieje w `voice_gateway`, inaczej dołożyć stałą `REFUSE_PATTERNS`); funkcja `should_refuse(text) -> (bool, matched_pattern)` |
| [ ] | 4.2 Zapisy odmów do `project_files/run_files/carplay_refusals.jsonl` i mijanek do `project_files/run_files/carplay_misses.jsonl` (jeden JSON na linię: `ts`, `session_id`, `transcript`, `candidates`, `pattern`); dopisywanie z lockiem na pliku |
| [ ] | 4.3 Testy odmowy: dla każdego wzorca z listy — jeden test; sprawdzian, że `send-keys` nie został wywołany (mock `subprocess.run`) |

### 5. Token wspólny HA ↔ bramka (po D10 — zastąpiło Shortcut iOS)

| Done | Task |
|---|---|
| [ ] | 5.1 Wygenerować wspólny token: `python -c "import secrets; print(secrets.token_hex(32))"`; zapisać w **obu** maszynach do `~/.claude/car_tokens.json` jako `{"token": "<hex>", "created": "<iso>"}` |
| [ ] | 5.2 Endpoint `/api/car/dispatch` czyta plik tokenów przy starcie bramki (funkcja `load_car_tokens()`); 401 gdy nagłówek `Authorization: Bearer <token>` nie pasuje |
| [ ] | 5.3 HA Claude: wartość tokenu w `rest_command_claude.yaml` jako `!secret car_token`, odpowiedni wpis w `secrets.yaml` na Pi |
| [ ] | 5.4 Dokumentacja rotacji w `notes/HANDOFF_carplay_okna.md`: jak podmienić token w obu miejscach bez przerwy > 60 s |

### 6. Prerejestracja i pomiar w jeździe

| Done | Task |
|---|---|
| [ ] | 6.1 PREREJESTRACJA (przed jazdą, ZASADY 3.3): hipoteza „≥ 7/10 udanych prób, mediana `koniec dyktowania → pierwsze słowo z głośnika` ≤ 20 s, ≥ 8/10 poprawnych transkrypcji nazwy projektu i promptu łącznie"; pytania: po jednym do trzech projektów (`Car_chatGPT_integration`, `project_integration`, `HA`), każde 3 razy, plus 1 test wygaśnięcia sesji po 11 min; definicja udanej próby = `send-keys` wykonany do właściwego projektu i `Glosowo:` dotarł audio zrozumiałym po polsku; **jedna** statystyka: mediana łącznego czasu; **liczba testowanych porównań: 1** (tylko ścieżka główna, nie porównujemy wariantów); poprawka na wielokrotność niepotrzebna; konfuzje: zasięg LTE/5G (zapis mocy sygnału przed każdą próbą), prędkość (zapis GPS), model TTS (`voice_choice.json` zamrożony); **warunek NEGATYWU**: mediana > 30 s albo udane < 5/10 ⇒ odrzucenie i powrót do design; **czego wynik NIE uprawnia**: nie mówi nic o rozmowie wieloturowej z pamięcią kontekstu, o poleceniach wymagających „yes/no" ani o jakości TTS poza polskim |
| [ ] | 6.2 Zasilanie peceta w pracy aktywne (`poc-carplay-command 1.7`); maszyna z tmux-ami 22 projektów nie zasnęła przez 2 h przed pomiarem (zapis `powercfg /requests`) |
| [ ] | 6.3 Jazda pomiarowa: ≥ 10 prób, ≥ 3 próby przy prędkości ≥ 70 km/h; tabela w `notes/HANDOFF_carplay_okna.md` z kolumnami: nr, pytanie, projekt rozpoznany, transkrypcja (OK/pomyłka), outcome (`sent`/`ambiguous`/`missing`/`refused`/`timeout`), t_dyktowanie [s], t_odpowiedz [s], prędkość [km/h], LTE/5G, uwagi |
| [ ] | 6.4 Opracowanie: policzyć statystyki, każdą nieudaną próbę przypisać do warstwy (Siri / Whisper / parser / resolve / send-keys / capture-pane / TTS / sieć); wpis negatywów jako negatywów (ZASADY 5.8) |
| [ ] | 6.5 Decyzja PoC (ZASADY 5.1): zaliczony / negatywny; wpis do HANDOFF; rekomendacja — czy iść dalej do iteracji drugiej (otwieranie okien głosem, polecenia yes/no), czy czekać |

### 7. Zamknięcie zmiany

| Done | Task |
|---|---|
| [ ] | 7.1 Usunięcie tymczasowego endpointu `/api/car/test-audio` z kroku 1.2; sprawdzian `grep -n "test-audio" project_integration/monitor/voice_gateway.py` |
| [ ] | 7.2 Notatka sesji wg szablonu (ZASADY 1.1) z liczbami z 6.3 |
| [ ] | 7.3 Aktualizacja `notes/start.md` sekcja „Ostatnia sesja" |
| [ ] | 7.4 `python notes/gen_openspec_status.py` → commit zaktualizowanego `openspec/STATUS.md` |
| [ ] | 7.5 Prośba o archiwum zmiany po pomiarze: `/opsx:archive carplay-okna-projektow` (wywołuje użytkownik) |

## voice-intent

`26/29` tasks complete.

### 1. Schemat i dane

| Done | Task |
|---|---|
| [x] | 1.1 Schemat intencji v1 opisany w `design.md` i w specyfikacji (`intent`, `repo`, `text`, `limit_zdan`, `v`); uzasadnienie kazdego pola, w tym dlaczego `text` zostaje cala wypowiedzia |
| [x] | 1.2 `poc/aliases.json`: tablica aliasow jako **dane** (klucz = nazwa kanoniczna repo, wartosc = mowione warianty), z `min_ratio` i wersja pliku; dodanie projektu nie wymaga zmiany kodu |
| [x] | 1.3 Nazwy kanoniczne czytane z `~/.claude/monitor_repos.env` (jedno zrodlo prawdy); alias wskazujacy na nieznane repo wypisywany przy starcie jako ostrzezenie, nie ignorowany po cichu |

### 2. Parser deterministyczny

| Done | Task |
|---|---|
| [x] | 2.1 `poc/intent.py`: `normalize()` (male litery, polskie znaki na ASCII, tylko `[a-z0-9 ]`) — wspolna podstawa wszystkich porownan |
| [x] | 2.2 `match_repo()`: dopasowanie aliasu po n-gramach slow o dlugosci aliasu, `difflib.SequenceMatcher`, prog `min_ratio` z pliku danych; zwraca `(repo, powod)` gdzie powod to `exact` / `fuzzy` / `explicit-all` / `ambiguous` / `no-match` (dwa repo blizej niz 0,02 od siebie to nie decyzja, tylko rzut moneta -> `*`) |
| [x] | 2.3 `parse_limit()`: „w jednym/dwoch/trzech/czterech/pieciu zdaniach" oraz cyfry („w 2 zdaniach"); brak liczby = `None`, bez zgadywania z „krotko" |
| [x] | 2.4 `parse()`: slowa kluczowe intencji (`note`, `queue`), domyslnie `ask`; zwraca pelna strukture v1 |
| [x] | 2.5 Zero dodatkowych wywolan modelu — decyzja i jej uzasadnienie w `design.md` („Rezerwa modelowa") |

### 3. Wpiecie w most

| Done | Task |
|---|---|
| [x] | 3.1 `ask_server.py` wola `intent.parse()` po transkrypcji, przed `ask_claude` |
| [x] | 3.2 `intent: note \| queue` -> HTTP 200 z jednym zdaniem odmowy po polsku (skrot czyta tresc, nie kod bledu); wpis w logu |
| [x] | 3.3 Rozpoznane `repo` zaweza zakres: `claude -p` startuje w tym katalogu i nie dostaje `--add-dir` do pozostalych |
| [x] | 3.4 Instrukcja zakresu w prompcie: odpowiedz zaczyna sie od nazwy repozytorium (zamiast pytania potwierdzajacego); limit zdan doklejany, gdy podany |
| [x] | 3.5 Log zapisuje `intent`, `repo` i **powod** dopasowania (`explicit-all` vs `no-match` to dwie rozne rzeczy, inaczej nie da sie policzyc trafnosci) |
| [x] | 3.6 Odpowiedz `?format=json` niesie strukture intencji, zeby dalo sie mierzyc bez czytania logu |

### 4. Testy nazywajace porazke (ZASADY 4.4)

| Done | Task |
|---|---|
| [x] | 4.1 Fixture wypowiedzi `project_files/python/tests/fixtures/wypowiedzi.json` z jawnym polem `zrodlo`: `log` (prawdziwa transkrypcja Whispera) albo `syntetyczna` (napisana recznie) |
| [x] | 4.2 Test: prawdziwa transkrypcja „Carcha gpt integration" trafia w `Car_chatGPT_integration` — porazka, ktorej zapobiega: parser dzialajacy tylko na poprawnie wymowionych nazwach |
| [x] | 4.3 Test: „zanotuj..." nie jest pytaniem, a odmowa nie ma kodu bledu — porazka: cicha zamiana zapisu w pytanie |
| [x] | 4.4 Test: brak dopasowania daje `*` z powodem `no-match`, a „wszystkie projekty" daje `*` z powodem `explicit-all` — porazka: pomiar trafnosci liczacy nierozpoznanie jako sukces |
| [x] | 4.5 Test: alias spoza mapy repozytoriow jest raportowany, a parser dziala dalej |
| [x] | 4.6 Sprawdzenie mutacja kazdego z powyzszych (wprowadz blad z powrotem, test ma paść) i zapis wyniku w notatce sesji |

### 5. Pomiar (PREREJESTRACJA przed przebiegiem, ZASADY 3.3)

| Done | Task |
|---|---|
| [x] | 5.1 **PREREJESTRACJA — trafnosc rozpoznania repozytorium.** *Hipoteza:* reguly + aliasy rozpoznaja wlasciwe repozytorium w **>= 80%** wypowiedzi, w ktorych projekt jest nazwany, przy odsetku falszywych trafien **<= 10%**. *Dane:* fixture `wypowiedzi.json`, **>= 40 wypowiedzi**, w tym >= 5 na kazde repo z mapy maszyny i >= 8 bez nazwanego projektu; kazda wypowiedz ma pole `zrodlo`. *Wykluczenia:* wypowiedzi, w ktorych czlowiek sam nie potrafi wskazac projektu, sa oznaczone `oczekiwane: "*"`, a nie usuwane. *Definicja etykiety:* trafienie = `repo` rowne `oczekiwane`; falszywe trafienie = `repo` to konkretne repo, a `oczekiwane` bylo inne albo `*`; uczciwe `*` nie jest trafieniem ani falszem. *Jedna statystyka:* odsetek trafien; druga (falszywe trafienia) jest **warunkiem bezpieczenstwa**, nie druga hipoteza. *Liczba testowanych porownan:* **1** (jeden prog `min_ratio` = 0,82 zadeklarowany z gory). Strojenie progu po zobaczeniu wynikow = dopasowanie do fixture i musi zostac zapisane jako takie. *Konfuzje do zmierzenia:* udzial wypowiedzi `zrodlo: log` w zbiorze (fixture napisany przy biurku jest latwiejszy niz mowa w aucie) i dlugosc aliasu (aliasy jednoslowne falszuja latwiej). *Warunek NEGATYWU:* trafnosc < 70% albo falszywe trafienia > 10% -> `repo` zostaje na stale `*`, konczymy i nie szukamy trzeciej heurystyki. *Czego wynik NIE uprawnia:* niczego o mowie w jadacym aucie — fixture to tekst, nie nagrania; liczba z prawdziwych nagran moze byc tylko gorsza. |
| [x] | 5.2 **PREREJESTRACJA — czy zawezenie zakresu skraca odpowiedz.** *Hipoteza:* przy rozpoznanym repozytorium mediana pelnej petli spada wobec zakresu „wszystkie". *Dane:* 10 pytan (5 par: to samo pytanie z zawezeniem i bez), ta sama maszyna, model bez zmian. *Jedna statystyka:* mediana czasu pelnej petli. *Liczba porownan:* 1. *Warunek NEGATYWU:* mediana nie spada albo rosnie -> zawezenie zostaje (mniejsza szansa na odpowiedz z cudzego repo), ale **nie wolno** go opisywac jako przyspieszenia. *Czego wynik NIE uprawnia:* zdania „zadanie 2.7 zrobione" — to osobny pomiar na innym zakresie. |
| [x] | 5.3 Przebieg 5.1 na fixturze i zapis liczb (trafienia, falszywe trafienia, rozbicie wg `zrodlo`) |
| [x] | 5.4 Przebieg 5.2 na tej maszynie i zapis liczb obok pomiarow z `notes/HANDOFF_most_pytan.md` **Wynik NEGATYWNY zgodnie z zadeklarowanym warunkiem**: mediana 14,0 s (zawezony) wobec 14,2 s (wszystkie), n=5+5 — roznica tonie w rozrzucie 11,8–25,2 s. Zawezenie zostaje jako ochrona przed odpowiedzia z cudzego drzewa i **nie jest** opisywane jako przyspieszenie. |
| [ ] | 5.5 **Slabe aliasy zmierzone 2026-09-16, poprawka wymaga drugiego pomiaru.** Przebieg 5.3 pokazal dwa aliasy, ktore lapia zwykle polskie zdania: `projekt car` trafia w „ktory **projekt** ma najwiecej otwartych zadan" (jedyne falszywe trafienie), a `kazdy projekt` z listy `wszystkie` trafia w „**czy projekt** integracji projektow ma cos pilnego". Usuniecie ich po zobaczeniu wynikow jest **strojeniem do fixture** (ZASADY 5.4) — dlatego: (1) najpierw dopisac >= 10 nowych wypowiedzi, ktore tego nie dotycza, (2) potem zmienic aliasy, (3) potem przemierzyc, i zapisac obie liczby obok siebie jako **drugie** porownanie, jawnie policzone |
| [ ] | 5.6 Nagrac >= 10 prawdziwych wypowiedzi przez `/ask` i dopisac transkrypcje do fixture z `zrodlo: log`; powtorzyc 5.1 i porownac z wersja syntetyczna |

### 6. Domkniecie

| Done | Task |
|---|---|
| [x] | 6.1 Notatka sesji z liczbami i `notes/start.md` (regula 1.1) |
| [x] | 6.2 `python notes/gen_openspec_status.py` |
| [ ] | 6.3 `notes/HANDOFF_most_pytan.md`: akapit o warstwie intencji i o tym, jak dodac projekt (jeden wpis w `poc/aliases.json`) |

## voice-grok-front

`0/24` tasks complete.

### 1. Warunki wstepne i porzadki (zanim powstanie kod)

| Done | Task |
|---|---|
| [ ] | 1.1 Potwierdzic plan Grok-a z „Bring Your Own MCP" i zapisac, ktory to plan i co kosztuje; bez tego cala grupa 3 jest bezprzedmiotowa i zostaje sciezka zapasowa |
| [ ] | 1.2 Przeczytac `osaighi/talk-to-claude-code` w calosci i spisac w `notes/research/`, co bierzemy (wzorzec `ask`/`get_reply`, endpointy `/voice/*`, Funnel), a czego nie (ich most do sesji — my mamy orchestrator); **nie kopiowac kodu bez przeczytania licencji** |
| [ ] | 1.3 Zmierzyc, czy orchestrator na pececie odpowiada na `POST /api/agent/chat` z tej maszyny i ile to trwa (3 proby, mediana) — to jest baza czasowa, wobec ktorej liczymy koszt frontu |
| [ ] | 1.4 Zaktualizowac naglowek `monitor/live_sessions.py`: wniosek „nie da sie wejsc do zywego okna" jest prawdziwy **dla CLI**, ale Remote Control (`/remote-control`, Pro/Max/Team/Enterprise) podlacza zywa sesje do claude.ai/code i aplikacji mobilnej — **recznie, bez API i bez CarPlay**. Zapisac obie polowy, zeby nikt nie szukal drugi raz |
| [ ] | 1.5 Zapisac w `notes/HANDOFF_most_pytan.md` podzial rol: Remote Control = telefon w reku, ten front = auto; to nie sa konkurenci |

### 2. Serwer MCP jako cienka warstwa

| Done | Task |
|---|---|
| [ ] | 2.1 `poc/grok_mcp.py`: narzedzia `ask(session, text)` i `get_reply(session)`; `ask` wraca natychmiast ze statusem `working`, `get_reply` oddaje `working` albo `done` z tekstem |
| [ ] | 2.2 Opis narzedzia `get_reply` **wprost** instruuje klienta do ponownego wywolania przy statusie `working` (to jedyne miejsce, gdzie zachowanie klienta zalezy od naszego tekstu) |
| [ ] | 2.3 Kazde zapytanie idzie do `POST /api/agent/chat` orchestratora; **zero wlasnego promptu, zero `claude`, zero wlasnej listy repo** |
| [ ] | 2.4 Test nazywajacy porazke: plik `grok_mcp.py` nie zawiera wywolania `claude` ani sciezek repozytoriow — mutacja (dopisac `subprocess.run(["claude", ...])`) ma go wywalic |
| [ ] | 2.5 Historia rozmowy: n ostatnich par na sesje, wygasanie, izolacja miedzy sesjami; test: dwie sesje nie widza swoich tur |
| [ ] | 2.6 Narzedzie `sessions` (tylko odczyt) na danych z `monitor/live_sessions.py`: repozytorium + zajete/bezczynne; test: prosba o zmiane w zajetym oknie konczy sie odmowa, nie forkiem |
| [ ] | 2.7 Endpointy zapasowe `/voice/ask` i `/voice/reply` z tokenem w sciezce i w query (Skroty iOS nie ustawiaja naglowkow); ten sam przebieg co przez MCP |

### 3. Wystawienie publiczne — dopiero po bramkach

| Done | Task |
|---|---|
| [ ] | 3.1 Limit tempa i log kazdego wywolania (wzorzec z `poc/ask_server.py`), zanim cokolwiek wyjdzie poza tailnet |
| [ ] | 3.2 Zapis **domyslnie wylaczony**; wlaczony idzie wylacznie przez `execute_worker` z jego bramkami i z potwierdzeniem glosem — bramki SHALL NOT byc omijane; test odmowy przy wylaczonym zapisie |
| [ ] | 3.3 Tailscale Funnel ze stabilna nazwa hosta; zapisac nazwe i sposob odtworzenia w HANDOFF |
| [ ] | 3.4 Test bezpieczenstwa: zly token -> 403 i wpis w logu; brak tokenu -> 403; token w query dziala tak samo jak w sciezce |
| [ ] | 3.5 Zapisac wprost w HANDOFF, ze od tego momentu endpoint jest **publiczny**, oraz co z repozytoriow wychodzi do xAI (prywatnosc jako decyzja, nie odkrycie) |

### 4. Prerejestracja i pomiar rozmowy

| Done | Task |
|---|---|
| [ ] | 4.1 PREREJESTRACJA (przed pierwszym przebiegiem, ZASADY 3.3): **hipoteza** — rozmowa wieloturowa utrzymuje kontekst przez >= 4 tury w >= 8/10 przebiegow, a czas do pierwszego slowa odpowiedzi ma mediane <= 20 s; **dane** — 10 rozmow po 5 tur, scenariusze spisane z gory, na postoju; **etykieta** — tura udana = odpowiedz zgodna z danymi monitora i odnoszaca sie do wlasciwej tury wczesniejszej; **jedna statystyka** — odsetek rozmow z zachowanym kontekstem do 4. tury; **liczba testowanych porownan: 2** (liczba tur w historii: 3 wobec 5); **poprawka na wielokrotnosc** — przy dwoch porownaniach raportujemy obie liczby, nie wybieramy lepszej po fakcie; **konfuzje** — dlugosc odpowiedzi orchestratora i to, czy klient rzeczywiscie odpytywal w petli (z logu); **warunek NEGATYWU** — jesli klient przestaje odpytywac przed koncem w > 2/10 przebiegow, front jest nieuzywalny i wracamy do sciezki zapasowej; **czego wynik NIE uprawnia** — nie mowi nic o jezdzie, o hasach w tle ani o zleceniach zapisujacych |
| [ ] | 4.2 Przebieg wg 4.1 na postoju; tabela do `notes/HANDOFF_most_pytan.md` |
| [ ] | 4.3 Liczba tur w historii wybrana **pomiarem** (3 wobec 5), nie zalozeniem; zapisac koszt czasowy kazdej dolozonej tury |
| [ ] | 4.4 Jazda: >= 10 tur, >= 3 rozne tematy, >= 3 tury przy predkosci >= 70 km/h; kazda nieudana tura przypisana do warstwy (klient / siec / orchestrator / model / odtwarzanie) |
| [ ] | 4.5 Wynik negatywny zapisac jako negatywny z przyczyna (ZASADY 5.8) — takze wtedy, gdy przyczyna lezy po stronie Grok-a |

### 5. Decyzja

| Done | Task |
|---|---|
| [ ] | 5.1 Wpis „Decyzja" w HANDOFF z liczbami: czy rozmowa w aucie dziala, na czym stoi, co kosztuje (subskrypcja, publiczny endpoint, prywatnosc), i czy `poc/ask_server.py` mozna wygasic |
| [ ] | 5.2 Aktualizacja `notes/start.md`, notatka sesji, `python notes/gen_openspec_status.py` |

## poc-carplay-command

`7/39` tasks complete.

### 1. Warunki wstępne

| Done | Task |
|---|---|
| [x] | 1.1 Spisać środowisko w `notes/HANDOFF_poc_carplay.md`: model iPhone'a, wersja iOS, wersja HA Companion, wersja HA Core, plan ChatGPT, Apple Intelligence, język Siri, dyktowanie polskie |
| [x] | 1.2 Sprawdzić, czy iPhone ma aktywny Tailscale w aucie na LTE; jeśli tak, endpoint pytań nie musi być publiczny — zapisać werdykt i czas odpowiedzi `/health` w ms |
| [ ] | 1.3 Wybrać maszynę w tailnecie na transkrypcję i `claude -p`; potwierdzić, że nie usypia, i zapisać jej nazwę oraz adres |
| [ ] | 1.4 Włączyć Siri z językiem angielskim i „Hey Siri" przy zablokowanym ekranie; potwierdzić, że w CarPlay reaguje |
| [ ] | 1.5 Sprawdzić wersję aplikacji HA Companion (wariant B wymaga 26.4+) |
| [ ] | 1.6 Pecet w pracy: uruchomić `poc/deploy/00_check.ps1` i zamknąć każde `TODO` (python, node, `claude` zalogowany, `faster-whisper` z `ctranslate2==4.5.0`, Tailscale, sklonowane repozytoria z `repos.txt`); zapisać wyjście skryptu w HANDOFF |
| [ ] | 1.7 Zasilanie peceta w pracy: `poc/deploy/01_power.ps1` (monitory 5 min, sen / hibernacja / dysk nigdy, **unattended sleep 0**, hibernacja wyłączona); po 10 minutach ciemnego ekranu sprawdzić `powercfg /requests` i zapisać, że maszyna nie zasnęła |
| [ ] | 1.8 Zadania `AskBridge\bridge\|watchdog\|gitpull` przez `poc/deploy/02_install_tasks.ps1` (z hasłem konta); test twardy: **restart peceta i odpowiedź z tailnetu bez logowania się na niego** |
| [ ] | 1.9 Zmierzyć `poc/deploy/check_bridge.ps1` na pececie w pracy (czas `/health` w ms, pełna pętla w ms, 3 próby) i wpisać liczby do `notes/HANDOFF_most_pytan.md` obok pomiarów z `desktop-ffshioa` |

### 2. Backend pytań w project_monitorze

| Done | Task |
|---|---|
| [x] | 2.1 Most pytań jako jeden plik `poc/ask_server.py` w tym repo (nie w project_monitorze — monitor stoi na RPi, a Claude i repozytoria są na pececie): przyjmuje audio albo tekst, sekret w ścieżce, limit tempa, log każdego wywołania, bind tylko na adres Tailscale |
| [x] | 2.2 Transkrypcja: faster-whisper lokalnie na maszynie z 1.3, język polski wymuszony; wariant zapasowy przez API transkrypcji, wybierany flagą konfiguracji |
| [x] | 2.3 Mózg: `claude -p` uruchamiany z dostępem **tylko do odczytu** repozytoriów, bez uprawnień do zapisu i `git push`; kontekst budowany z `/api/state`, zadań i zdarzeń monitora oraz plików `notes/` |
| [ ] | 2.4 Odpowiedź: zwięzły tekst po polsku, przycięty do długości sensownej do przeczytania głosem; przy długim zadaniu odpowiedź natychmiastowa „przyjąłem" plus powiadomienie HA z wynikiem |
| [x] | 2.5 Test z komputera: `curl` z plikiem audio po polsku i z samym tekstem; potwierdzić poprawną transkrypcję, sensowną odpowiedź i wpis w logu |
| [ ] | 2.6 Test odmowy: pytanie proszące o commit lub push ma zostać odrzucone i zapisane w logu |
| [ ] | 2.7 Skrócić czas odpowiedzi: budować kontekst po stronie mostu (STATUS.md, nagłówki start.md, ostatnie commity) i wkładać go do promptu, żeby model nie szukał w plikach; zmierzyć wobec dzisiejszych 13–34 s |

### 3. Skrót iOS (na postoju)

| Done | Task |
|---|---|
| [ ] | 3.1 Zbudować skrót „Monitor": `Record Audio` o stałej długości → POST do `/api/ask` → `Speak Text` polskim głosem; wyłączyć pytanie o zgodę |
| [ ] | 3.2 Zmierzyć dwie długości nagrania (6 s i 10 s) po 3 próby; wybrać po wynikach, nie po wrażeniu |
| [ ] | 3.3 Test „Hey Siri, Monitor" na telefonie bez CarPlay: 3 próby; potwierdzić, że nagranie startuje i kończy się samo, bez dotykania ekranu |
| [ ] | 3.4 Test na postoju z CarPlay: 3 próby; potwierdzić, że sygnał startu i odpowiedź idą przez głośniki auta |
| [ ] | 3.5 Wariant zapasowy A: drugi skrót z `Dictate Text` i locale `pl_PL` zamiast nagrania; sprawdzić `Show Result`, czy tekst ma polskie znaki; 3 próby na postoju |
| [ ] | 3.6 Wariant zapasowy B: w HA Companion → CarPlay → Quick Access dodać Assist; 3 próby na postoju, świadomie na frazach zadeklarowanych w `voice_data.yaml` |
| [x] | 3.7 Wariant C („Monitor GPT", jedyna droga do głosu ChatGPT): most oddaje fakty zamiast zdania pod `?style=facts`, a zdanie układa akcja **Ask ChatGPT** w Skrócie; kroki skrótu w `notes/HANDOFF_most_pytan.md`, uzasadnienie i weryfikacja źródeł w `notes/research/2026-09-22-chatgpt-voice-weryfikacja.md` |
| [ ] | 3.8 PREREJESTRACJA wariantu C (przed pomiarem, ZASADY 3.3): **hipoteza** — wariant C jest zrozumiały nie gorzej niż wersja 1 i kosztuje nie więcej niż 4 s mediany; **dane** — te same 3 pytania co w 5.1, po 5 prób wersji 1 i 5 prób wariantu C, ta sama maszyna, ten sam model mostu, na postoju; **etykieta** — próba udana = odpowiedź zgodna z danymi monitora i słyszalna po polsku; **jedna statystyka** — mediana czasu od końca dyktowania do pierwszego słowa odpowiedzi; **liczba testowanych porównań: 1** (C wobec wersji 1), świadomie osobno od trzech porównań z 5.1, żeby nie rozdmuchiwać wielokrotności; **poprawka** — niepotrzebna przy jednym porównaniu, ale wynik nie może być raportowany łącznie z 5.1 jako „cztery warianty"; **konfuzje** — długość odpowiedzi mostu (facts bywa dłuższe) i model wybrany w akcji ChatGPT, oba zapisywane przy każdej próbie; **warunek NEGATYWU** — mediana dłuższa o > 4 s bez poprawy zrozumiałości ⇒ wariant odrzucony i nie strojony dalej; **czego wynik NIE uprawnia** — nie mówi nic o jeździe, o rozmowie wieloturowej ani o tym, że ChatGPT Voice wywołuje cokolwiek sam |
| [ ] | 3.9 Pomiar wariantu C wg 3.8 na postoju; tabela prób do `notes/HANDOFF_most_pytan.md` obok pozostałych wariantów; wynik negatywny zapisać jako negatywny z przyczyną (ZASADY 5.8) |

### 4. Scena testowa w Home Assistancie (twardy ślad pętli)

| Done | Task |
|---|---|
| [ ] | 4.1 W repo `HA` dodać scenę `scene.poc_carplay_test` z widocznym efektem; frazy dopisać w `voice/voice_data.yaml` i wygenerować przez `voice/gen_voice_sentences.py`, nie ręcznie w dwóch plikach |
| [ ] | 4.2 Wyeksponować scenę do Assist przez WebSocket `homeassistant/expose_entity`; potwierdzić z panelu |
| [ ] | 4.3 Umożliwić wykonanie polecenia z `/api/ask`: rozpoznane polecenie do HA idzie do lokalnego Assist, a nie do modelu; 3 próby z komputera |
| [ ] | 4.4 Potwierdzić, że potok głosowy HA pozostał w pełni lokalny i nie dodano agenta chmurowego |

### 5. Prerejestracja i pomiar w jeździe

| Done | Task |
|---|---|
| [ ] | 5.1 PREREJESTRACJA (przed jazdą): hipoteza „ścieżka główna daje ≥ 7/10 udanych prób, medianę czasu odpowiedzi ≤ 15 s i ≥ 8/10 poprawnych transkrypcji”; pytania: „co się dzieje z projektem Car ChatGPT”, „ile zadań zostało w projekcie X”, „kiedy była ostatnia sesja w repozytorium HA”, plus polecenie „włącz scenę testową”; definicja udanej próby = odpowiedź zgodna z danymi monitora i słyszalna po polsku; statystyki: udane/wszystkie, transkrypcje poprawne/wszystkie, mediana i max czasu; liczba testowanych porównań: 3 (ścieżka główna, wariant A, wariant B); warunek negatywu jak w spec; wynik nie uprawnia do wniosków o rozmowie wieloturowej ani o operacjach zapisujących |
| [ ] | 5.2 Protokół rejestracji: nagranie audio z timestampem plus log endpointu i logbook HA; tabela prób w HANDOFF z kolumnami: nr, pytanie, wariant, wynik, transkrypcja OK?, trafność, t_odpowiedz [s], prędkość, uwagi |
| [ ] | 5.3 Jazda pomiarowa: ≥ 10 prób ścieżki głównej, ≥ 3 różne pytania, ≥ 3 próby przy prędkości ≥ 70 km/h |
| [ ] | 5.4 Ta sama jazda: ≥ 5 prób wariantu A; jeśli wersja aplikacji pozwala, ≥ 5 prób wariantu B |
| [ ] | 5.5 Opracowanie: policzyć statystyki z nagrania i logów, wpisać do HANDOFF; każdą nieudaną próbę przypisać do warstwy (Siri / nagranie / transkrypcja / sieć / model / odtwarzanie) |
| [ ] | 5.6 Porównać transkrypcję Whispera z `Dictate Text` na tych samych nagraniach z hałasu — to rozstrzyga, czy warstwa Apple wystarcza |

### 6. Eksperyment E1 (tani test, niezależny od reszty)

| Done | Task |
|---|---|
| [ ] | 6.1 Wystawić publiczny adres z logiem user-agenta, IP i czasu; poprosić ChatGPT o jego otwarcie w tekście, głosem i głosem w CarPlay, po 3 próby |
| [ ] | 6.2 Werdykt: czy w logu pojawia się `ChatGPT-User` z IP z listy OpenAI, czy treść wraca wiernie czy streszczona, jakie opóźnienie, czy powtórka nie idzie z cache; zapis do HANDOFF jako osobna tabela |

### 7. Decyzja i zamknięcie

| Done | Task |
|---|---|
| [ ] | 7.1 Wpis „Decyzja" w HANDOFF: PoC zaliczony / negatywny, z liczbami; osobne zdania o transkrypcji polskiej, o czasie odpowiedzi i o wyniku E1; rekomendacja, czy budować Command Center i na jakim wejściu |
| [ ] | 7.2 Aktualizacja `notes/start.md`, notatka sesji, `python notes/gen_openspec_status.py` |

## ask-core-client

`1/16` tasks complete.

### 1. Zależność od rdzenia

| Done | Task |
|---|---|
| [x] | 1.1 Sprawdzić, że `monitor/ask_core.py` jest w tym repo (dostarcza `install_pack.py` z `project_integration`); jeśli nie ma — `python tools/install_pack.py <to repo> --apply` po stronie monitora i `git pull` **Potwierdzone 2026-09-16**: `monitor/ask_core.py` (306 linii) przyszedł paczką z `project_integration`, drzewo czyste i zgodne z `origin/main`, 25 testów zielonych. Sygnatura: `ask(paths, question, system=, model=, timeout=, context=, use_digest=False) -> (answer, error)`, nigdy nie rzuca; `refresh_repo` / `refresh_all` / `for_speech` / `digest` na miejscu. |
| [ ] | 1.2 PREREJESTRACJA pomiaru: przed zmianą zmierzyć obecne 10 pytań (mediana i p90 pełnej pętli oraz samego `claude`), zapisać w notatce; warunek negatywu: jeśli po przejściu na rdzeń mediana rośnie o > 15%, wracamy do własnego `ask_claude` i mówimy dlaczego |

### 2. Przeniesienie świeżości do rdzenia (nasz wkład)

| Done | Task |
|---|---|
| [ ] | 2.1 `sync_repo` → `ask_core.refresh_repo(path, timeout)` bez zmiany semantyki: `pull --ff-only` tylko przy czystym drzewie, nigdy rebase, nigdy push; zwraca stan („podciagniete z remote" / „bez zmian na remote" / „lokalne zmiany, nie odswiezam" / „NIE odswiezone") |
| [ ] | 2.2 `sync_all` → `ask_core.refresh_all(paths, timeout)` (równolegle, jak dziś: zmierzone 1,95 s dla czterech repo) |
| [ ] | 2.3 Testy z `project_files/python/tests/test_ask_server.py` dotyczące świeżości przenieść do paczki razem z kodem; tutaj zostaje test, że `ask_server` **woła** rdzeń (a nie że rdzeń działa) |

### 3. `ask_server.py` jako klient

| Done | Task |
|---|---|
| [ ] | 3.1 `ask_claude(question)` → `ask_core.ask(REPOS, question, system=SYSTEM, model=MODEL, timeout=CLAUDE_TIMEOUT)`; `SYSTEM` (kierowca: trzy zdania, bez markdown) zostaje w tym repo jako parametr |
| [ ] | 3.2 `for_speech` → `ask_core.for_speech`; usunąć lokalną kopię po potwierdzeniu, że testy na bloki kodu i znaki markdown przechodzą na wersji z rdzenia |
| [ ] | 3.3 `repo_paths()`: domyślnie `~/.claude/monitor_repos.env`, `ASK_REPOS` / `ASK_ROOT` jako nadpisanie; test: pusta mapa i brak zmiennych → czytelny błąd, nie cisza |
| [ ] | 3.4 Sprawdzić na tej maszynie, że pytanie z limitem („w dwóch zdaniach") rzeczywiście dociera do modelu — rdzeń przekazuje pytanie przez **stdin**, nie w argv (defekt monitora z 2026-09-16); test: żaden element argv nie zawiera `\n` |
| [ ] | 3.6 **Digest: liczby z monitora NIE przenosza sie tutaj** (sesja `project-integration-34`, 2026-09-16). Tam `use_digest=True` dalo mediane 18,4 -> 12,3 s (-33,2%, 9/10 par szybszych), ale **inny prompt (kierowca, trzy zdania), inny model (sonnet) i inny zestaw repo** — ich prerejestracja wprost odmawia wniosku o tej sciezce. Dwie rzeczy wazniejsze od mediany dla nas: (1) **ogon prawie sie nie ruszyl** (p90 26,1 -> 22,9 s, -12%), a to wlasnie ogon decyduje o progu 15 s pelnej petli — digest przesuwa srodek rozkladu, nie najgorszy przypadek; (2) jedna para **zwolnila dwukrotnie** (18,8 -> 35,0 s) przy dluzszej odpowiedzi, u nich otwarte zadanie 3.8. Wniosek: digest wlaczamy **tylko z wlasnym pomiarem** (przebieg naprzemienny w parach, jak w naszym voice-intent 5.2), i deklarujemy **p90, nie mediane**, bo to p90 decyduje o naszym progu. |
| [ ] | 3.5 Powtórzyć pomiar 1.2 i porównać z prerejestracją; liczby w notatce sesji |

### 4. Jeden rezydent na maszynę

| Done | Task |
|---|---|
| [ ] | 4.1 `poc/deploy/02_install_tasks.ps1`: dodatkowe zadanie „przy logowaniu" → `python <repo>\monitor\ask_worker.py --spawn` (idempotentne: worker sam sprawdza blokadę i wychodzi, gdy inny działa) |
| [ ] | 4.2 `poc/deploy/check_bridge.ps1`: pokazać też stan workera (`ask_worker.py --status`) |
| [ ] | 4.3 `poc/deploy/README_PRACA.md`: jeden akapit, że pecet w pracy odpowiada wtedy **obiema** drogami — głosem z auta i na pytania z Home Assistanta |

### 5. Domknięcie

| Done | Task |
|---|---|
| [ ] | 5.1 Notatka sesji z liczbami (przed/po) i wpis w `notes/start.md` |
| [ ] | 5.2 Zaznaczyć w `project_integration/openspec/changes/ask-core/tasks.md` zadania 2.2 i 2.3 jako zrobione po stronie klienta |
