# Sesja 2026-10-12 — CarPlay/HA pilny sprint (autonomiczna pętla profesor-student)

## Co zrobiono

Pętla autonomiczna od 22:32 do około 02:30 (4 h) na prośbę użytkownika: „Project Integration
ma działać dobrze, jak najwięcej funkcji głosowych w aucie przez HA, naprawy pilne."

**Endpointy bramki** (`project_integration/tools/voice_gateway.py`):
- `POST /api/car/dispatch` — główny dyspatcher, parser „do okna X / kontynuuj / prefiks"
  w `parse_car_prompt`, rejestr sticky session TTL 600 s, timeout 30 s, odmowy pisujące
  (`git push`, `rm -rf`, `sudo`, …)
- `GET /api/car/status` — agregat `/api/state` do krótkiego Głosowo
- `POST /api/car/open` — subprocess `okno.py`, idempotentne
- `GET /api/car/project/<name>/summary` — konkretny projekt, fuzzy
- `POST /api/car/todo` — zapisuje do `~/.claude/carplay_todos.jsonl`
- `POST /api/car/zamknij` — kasuje sticky sesję
- `POST /api/car/powtorz` — powtarza ostatnie Głosowo (sesja trzyma `last_text`)
- `GET /api/car/test-audio` + `/api/car/test-text` — diagnostyka Siri Shortcut PoC (zdane, do usunięcia)

**Rozszerzenie `okna.resolve`**: 4-ty tier **token-match** — dla query ≥ 2 słów każdy token musi
być podciągiem znormalizowanej nazwy. Rozwiązuje „car integration" → `Car_chatGPT_integration`
(wcześniej fail, bo „carintegration" nie jest podciągiem „carchatgptintegration").

**Pure helpers do testów**: `build_car_status_text(data)`, `build_car_project_text(rec, resolved)`,
`parse_car_prompt`, `car_sessions_*`, `load_car_tokens`, `should_refuse_car`.
Łącznie 46 testów w `tools/tests/test_car_dispatch.py` (1 świadomy skip).

**HA strona (okno `HA` tmux, w kooperacji z HA Claude)**:
- Nowe intenty: `DispatchClaude`, `PomocClaude`, `TestClaude`, `StatusClaude`, `OtworzOknoClaude`,
  `PodsumowanieClaude`, `ZapiszZadanie`, `ZamknijClaude`, `PowtorzClaude` (ten ostatni w robocie)
- `rest_command_claude.yaml`: `claude_dispatch`, `claude_status`, `claude_open`, `claude_summary`,
  `claude_todo`, `claude_zamknij` z nagłówkiem `!secret car_token_header`
- **Fix TTS**: `script.zapowiedz` używa teraz `tts.speak` przez serwer prywatnych głosów (Sznuk),
  nie Pipera (commit HA d025d8e)
- Warianty wyzwalaczy: `claude|klod|klot|klon|klok|klaud|klołd|cloud` (STT w CarPlay różnie
  transkrybuje; dołożone po logu bramki)

**Dokumentacja**:
- `notes/HANDOFF_carplay_okna.md` — Shortcut A/B/C, tabele pomiarowe PoC
- `notes/HANDOFF_car_endpoints.md` — 337 linii kontraktu HTTP ze schematami JSON, autoryzacją,
  rejestrem sesji, odmowami, 4-tier resolve, wzorcami rest_command (wygenerowane przez Agent)
- `poc/car_test_watch.py` — watcher logu dla pomiaru PoC z komputera
- `poc/gen_car_test_pdf.py` + PDF v2 ze ściągą 8 kategorii komend (wygenerowane i wysłane
  mailem przez Agent)

**OpenSpec**: `openspec/changes/carplay-okna-projektow/` zwalidowany (`openspec validate --strict`),
`STATUS.md` zregenerowany. Grupy nowe: 1.5 (HA Assist), 2a (status/open/project), 2b (todo/zamknij/powtorz).

## Kluczowe decyzje / zmiany semantyki

- **Porzucenie Siri Shortcut jako wejścia** (D10 w design.md). Siri zamyka sesję audio
  Shortcuta po ~1 s; `Odtwórz dźwięk` urywa „test głosu w a...". Przełącznik na HA Assist
  w CarPlay (kafelek Quick Access w HA Companion), bo HA ma własną sesję audio i Sznuka.
  Siri Shortcut zostaje jako diagnostyka Tailscale/certyfikatu.
- **Parser prefiksu „projekt" żyje w bramce, nie w HA sentences.** Speech-to-Phrase ma
  statyczny słownik; nazwy projektów nie są w nim. HA posyła całość przez wildcard `{pytanie}`,
  bramka `parse_car_prompt` rozbija na project+prompt, resolve 1-/2-/3-słowowe.
- **4-ty tier token-match w `okna.resolve`** — żeby „car integration" działało. Pure zmiana,
  wszystkie dotychczasowe testy przeszły, +4 nowe.
- **Dispatcher nie generuje audio** — zwraca JSON z `text`, HA robi TTS przez `script.zapowiedz`
  z VCC Sznukiem. Rozdzielenie: bramka = dispatcher, HA = pipeline PL + głos.

## Aktywne TODO / pending

- **Weryfikacja z auta**: użytkownik powinien na następnej jeździe sprawdzić:
  - Czy PowtorzClaude działa (dopiero po reload HA)
  - Czy TTS brzmi Sznukiem na wszystkich komendach (nie tylko ZapytajClaude)
  - Czy turn_on hijacking jest zaadresowany (HA Claude w robocie, ostatni log pokazywał
    `klot do okna project integration` → `turn_on project_integration` 0.83 confidence)
- **Zarchiwizować `carplay-okna-projektow`** po dojrzałym pomiarze PoC serii C (3 próby
  w aucie — jedna próba zdana „test głosu w aucie" Twoim głosem, trzeba ≥ 2/3)
- **Usunąć endpointy `/api/car/test-audio` i `/api/car/test-text`** (task 7.1) po zakończeniu
  zmiany

## Pliki zmienione

Dwa repozytoria:

**`project_integration`** (pushed, 4 commity, HEAD = `37d63f7`):
- `tools/voice_gateway.py` — +6 endpointów car/*, +5 pure helperów, +3 session helper fns
- `tools/okna.py` — 4-ty tier token-match w `resolve()`
- `tools/tests/test_car_dispatch.py` — 46 testów (parser, odmowy, sesje, tokeny z BOM/rotacja,
  pure helpers status/project, 4-tier resolve, zamknij)

**`Car_chatGPT_integration`** (do commitu w tej turze):
- `openspec/changes/carplay-okna-projektow/` — proposal, design (10 decyzji, 10 ryzyk),
  spec (8 wymagań, 15 scenariuszy), tasks (7 grup + 1.5/2a/2b, ~55 zadań)
- `notes/HANDOFF_carplay_okna.md` — Shortcut PoC + tabele
- `notes/HANDOFF_car_endpoints.md` — 337 linii kontraktu HTTP
- `notes/sesje/2026-10-12-carplay-ha-pilny-sprint.md` — ta notatka
- `poc/car_test_watch.py` — watcher logu
- `poc/gen_car_test_pdf.py` + wygenerowany PDF v2 (poza repo)
- `openspec/STATUS.md` — zregenerowany
- `project_files/run_files/petla_2026-10-12/petla_rejestr.md` — rejestr pętli

**`HA`** (commity przez HA Claude okno, pushed):
- `voice/claude_sentences_pl.yaml` — 7+ intentów głosowych + warianty klod/klot/klon/klok
- `voice/claude_intent.yaml` — akcje intentów + fix TTS zapowiedz
- `voice/rest_command_claude.yaml` — 6 rest_commands do bramki
- `secrets.yaml` — `car_token_header`

## Pomiary (stan końcowy 2026-10-13 ~02:30)

Finalne liczby po 4h autonomicznej pętli:

- **12 endpointów bramki** (`/api/car/*`): dispatch, status, open, project/<name>/summary,
  todo, zamknij, powtorz, ostatnie_todo, projekty, metryki, test-audio, test-text
- **11 intentów HA**: DispatchClaude, ZapytajClaude, TestClaude, PomocClaude,
  StatusClaude, OtworzOknoClaude, PodsumowanieClaude, ZapiszZadanie, ZamknijClaude,
  PowtorzClaude, OstatnieTodoClaude (plus MetrykiClaude w robocie)
- **Testy bramki**: 60 passed, 1 skipped w `test_car_dispatch.py`;
  dodatkowo 29 w `test_okna.py`. Łącznie **89 passed** w PI
- **Self-test**: `poc/car_selftest.py` — **15/15 PASS** w ~38 s
- **Metryki wywołań w 24h** (z `/api/car/metryki`): łącznie 121+;
  dispatch 32, poc 30, status 13, project 11, todo 11, open 8, zamknij 7, todos 5,
  projekty 3, powtorz 1
- **Commity**: 10 w `project_integration` (wszystkie pushed), 5 w `Car_chatGPT_integration`
  (pushed), ok. 8 w `HA` (HA Claude, pushed)
- **Fix TTS**: HA Claude commit d025d8e — `script.zapowiedz` używa `tts.speak` przez
  serwer prywatnych głosów (VCC Sznuk) na wszystkich komendach
- **Fix turn_on hijacking**: HA Claude commit d025d8e — 22 encje `input_boolean.pm_*`
  przemianowane w entity_registry na „PM <nazwa>", `wlacz project_integration` →
  `no_match`
- **Rozszerzenie `okna.resolve`**: 4-ty tier token-match (dla ≥ 2 słów każdy token
  jako podciąg znormalizowanej nazwy). „car integration" → `Car_chatGPT_integration` OK
- **Thread safety**: `threading.Lock` wokół RMW sekwencji w rejestrze sesji
  (`car_set_active`, `car_update_last_text`, `_car_zamknij`); test 20 wątków → 20
  session_id w rejestrze (bez race zostaje 1)
- **Odmowy pisujące**: `CAR_REFUSE_PATTERNS` rozszerzony z 11 do **23 wzorców**
  (powershell, iex, |sh, |bash, del /s, rmdir /s, chmod 777, dd if=, mkfs, rm -fr,
  rm --recursive) + 12 nowych testów parametrycznych
- **Dokumentacja**: `HANDOFF_car_endpoints.md` 430+ linii, PDF ściąga v3 (3 wersje
  wysłane mailem w ciągu dnia), notatka sesji, 2 subagenty do dokumentacji i PDF
- **Code review subagent** (fable-independent): 0 BLOCKER, 4 NICE-TO-HAVE, 2 COSMETIC,
  wszystkie 4 NICE-TO-HAVE zaadresowane (dedup auth, rozszerzone refuse, race condition
  lock, rozszerzenie testów)

### Dojrzałość endpointów Z23–Z25 (druga połowa pętli)

**Z23** — `POST /api/car/stop` zbudowany, pomiar 1-shot 347 ms, test nazywający porażkę (ZASADY 4.4),
self-test 15→17 PASS. Task 2c.9.

**Z24** — pomiar e2e `/stop` x 10 prób z pecetu (symulacja telefonu, user offline).
Prerejestracja w commit 92610a0 PRZED pomiarem (ZASADY 3.3). Wynik: **ZALICZONE 3/3 miar**:
- Miara 1 latencja [ms]: min 298.2 / median 309.5 / p90 325.4 / max 326.2 (progi 1500/2500)
- Miara 2 skuteczność `send-keys`: 10/10 `capture-pane` zmienione
- Miara 3 HTTP 200: 10/10 (zero timeout / 5xx)
Wariancja 28 ms rozstępu. Zapis `project_files/run_files/stop_e2e_2026-10-12-233411.jsonl`.
NIE uprawnia do: obciążenia (10 prób), każdego pane (1 pane), LTE OK (symulacja z pecetu).

**Z25** — Code review 2 + mutation test (ZASADY 4.4 druga połowa). Prerejestracja commit 4f5e54f.

- **M1 Code review 2 KRYT 1**: `send-keys -t =<session>:` idzie do **aktywnego pane sesji**, nie
  konkretnego. Przy sesji wielo-okiennej Ctrl-C poleci do złego pane. Dodatkowo `claude -p` ma
  własny signal handler. Text „stopnieto X" kłamie. **Decyzja projektowa, wymaga nowego
  proposal** (zapisane w `notes/HANDOFF_voice_gateway.md`, zadanie „WYMAGA PROJEKTU" w tasks.md).
- **M1 KRYT 2**: `outcome="timeout"` dla `rc != 0` bez timeoutu. Fałszywe mapowanie klasy błędu.
  Fix lokalny 5 min; nie zrobiony w Z25 na decyzję profesora (nie poprawiać przy okazji).
  Zapisane w tasks.md jako „FIX lokalny z warunkiem akceptacji".
- **M2 Mutation test NEGATYW** (ZASADY 5.8): `test_stop_bez_pane_zwraca_400_nie_500` **PRZESZEDŁ**
  mimo mutacji `rc == 0` → `rc != 0`. Przyczyna: test pokrywa branch `brak pane → 400`
  (pre-send-keys), mutacja jest post-send-keys. **ALE** self-test live **ZŁAPAŁ** mutację
  (zwrócił `outcome="timeout"` zamiast `"sent"`). **Wniosek**: ZASADY 4.4 spełnione dla
  integration self-test, nie dla pytest jednostkowego. Pytest nie pokrywa sukces-branche
  semantyki `send-keys`.
- **M3 Kod przywrócony**: `git diff tools/voice_gateway.py` pusty po przywróceniu mutacji
  (zweryfikowane mechanicznie).

**Własne błędy Claude'a w sesji** (ZASADY 1.3):

- Pytest `test_stop_bez_pane_...` obiecywał nazwą więcej niż pokrywał (reguła 4.4 spełniona
  nominalnie, nie merytorycznie). Znalazło się TYLKO dlatego, że mutation test uruchomiono
  z integracją self-testową równolegle. Lekcja: nazwa testu musi odpowiadać faktycznemu
  pokryciu (branch pre- vs post-send-keys to różne rzeczy).
- Pomiar 1-shot (Z23 pomiar 347 ms) nie jest dystrybucją — ZASADY 5.3 „kontrola odtworzenia
  przed walidacją" była ignorowana do Z24 (10 prób). Profesor to wyłapał.
- Początkowo odpaliłem pętlę profesor-student bez Agenta profesora (tylko register). Dopiero
  po hook feedback „nie kończ, melduj profesorowi" uruchomiłem Agent model=opus jako profesor.
  Lekcja: skill mówi profesor Z model=fable, ale Agent tool wspiera tylko sonnet/opus/haiku —
  trzeba było zapisać odstępstwo w Z0 od razu, nie czekać do hook.

### Z29b — diagnoza fallującego testu w PI (noc 2026-10-13, nie naprawa, ZASADY 3.1)

Pełna suita `pack/tests` i reszta w `project_integration` ujawniła 1 fail:

**Plik**: `project_integration/pack/tests/test_voice_tts_routing.py:376`

**Co pada**: `_post(url + "\voice\ask-text", {"text": "..."})` — `TimeoutError: timed out`
po 10 s w `recv_into`.

**Przyczyna wyjściowa** (literówka): Python interpretuje escape sequences `\v` i `\a`
w stringu bez prefiksu `r"..."`. W rezultacie URL zawiera `\x0b` (vertical tab) i `\x07`
(bell) zamiast `/voice/ask-text`. HTTP server nie rozpoznaje ścieżki, zwisa z recv_into,
pytest timeout.

**Werdykt**: osobne zadanie — nie moja iteracja (ZASADY 3.1, osobny temat = osobna zmiana).
Fix jest jednolinijkowy (`"\voice\ask-text"` → `"/voice/ask-text"`), ale nie wchodzi w zakres
Z29. Zapisane jako TODO do rozwiązania w kolejnej sesji.

**Status**: fail siedzi w HEAD przed Z28 (zweryfikowane — mój commit cee5b32 nie
dotknął `pack/tests/test_voice_tts_routing.py`). Nie regresja Z28.

### Z29a — mutation test wrappera `_resolve_window_with_aliases` (ZASADY 4.4 druga połowa)

Prerejestracja Z29a w commit 49e0d2a (ZASADY 3.3 przed mutacjami).

**4 mutacje × 4 testy, próg 4/4** (ZASADY 5.4 — dokładnie 4, nie więcej):

| mutacja | gałąź w kodzie | test | wynik |
|---|---|---|---|
| M1 | wyłącz mapowanie (zawsze `resolver_fn`) | `test_wrapper_aliasow_mapuje_fraze_do_kanonu` | **FAILED** |
| M2 | fallback `[]` dla fraz spoza aliases | `test_wrapper_aliasow_fallback_do_resolver_dla_fraz_spoza` | **FAILED** |
| M3 | pusty cache → `[]` zamiast fallback | `test_wrapper_aliasow_pusty_cache_zachowuje_sie_jak_resolver_solo` | **FAILED** |
| M4 | cichy fallback dla 4xx (zamiast raise) | `test_wrapper_aliasow_4xx_rzuca_wyjatek_do_gory` | **FAILED** |

**Wynik: 4/4 mutacji wykrytych** → próg spełniony → DECYZJA: ZALICZONE.

Kod przywrócony po każdej mutacji. `git diff tools/voice_gateway.py` pusty po Z29a.
Finalny pytest: **68 passed** w `test_car_dispatch.py` (bez regresji z Z28). Mutacje
nie commitowane (łamałyby produkcyjny kontrakt).

**Wynik NIE uprawnia** (ZASADY 5.14): do pełnego pokrycia semantycznego wrappera.
Mierzy tylko 4 gałęzie decyzyjne, nie wszystkie możliwe nieprawidłowe implementacje.
Nie bada kontraktu `_car_cached_aliases` wobec HTTPS tailnetowego (tylko ścieżki błędne).

### Z29c-fix — dokumentacja decyzji „nie normalizujemy diakrytyki" + test `data: {}` (noc 2026-10-13)

Po Z29c (0 KRYT) profesor zalecił fiksy w kolejności: **dokumentacja pierwsza**, test
drugi — bo decyzja w głowie teraz, test może odkryć coś nieoczekiwanego i decyzja
wyleci z pamięci.

**Komentarz w kodzie** (`voice_gateway.py:1073`): DECYZJA 2026-10-13 z konkretnym
warunkiem odwrócenia. Format z profesora: nie „nie normalizujemy, bo tak", tylko
„odwróć gdy X% zapytań z telefonu zawiera niepusty NFKD-diff + prerejestracja z progami
M1/M2 dla znormalizowanej ścieżki". Bez konkretnego warunku komentarz staje się
przesądem (ZASADA 0 ZASADY_PRACY.md).

**Odsyłacz w HANDOFF** (`notes/HANDOFF_car_endpoints.md`): jedno zdanie z linkiem do
`voice_gateway.py:1073` — druga maszyna znajdzie decyzję bez czytania kodu, ale treść
jest w jednym miejscu („dwa miejsca prawdy to zero miejsc prawdy").

**Test** (`test_wrapper_aliasow_pusty_dict_cache_fallback_do_resolver`): dla
`alias_map = {}` (Orchestrator ma 0 projektów lub tylko puste listy aliases) wrapper
deleguje do `resolver_fn`. Pytest **68 → 69 passed** (+1).

**Commity**: PI `87b4966`, Car `6ef94de`.

### Z29c — code review 3 wrappera `_resolve_window_with_aliases` + 4 testów

**Wynik**: 0 krytyczne / 2 średnie / 3 nice-to-have. **Wyrok: NA PÓŹNIEJ** — żadne znalezisko
nie podważa Z28 ani Z29a. Dołożenie teraz łamałoby prerejestrację i ZASADY 5.3.

**Średnie znaleziska (do następnej iteracji wrappera)**:
1. `voice_gateway.py:1083` — normalizacja `q = query.lower().split()` nie obsługuje
   diakrytyki. „ribnikstér" ≠ „ribnikster" w `aliases.json`. Decyzja projektowa, ale
   nieudokumentowana i bez testu.
2. `voice_gateway.py:1092` — wrapper normalizuje `q` **przed** `resolver_fn(q)`,
   czyli resolver dostaje inny input niż bez wrappera. Zmiana semantyki o którą
   nikt nie prosił (ZASADY 4.9 w literze). Test `pusty_cache_zachowuje_sie_jak_resolver_solo`
   używa już-znormalizowanych fraz (`"car"`, `"panda"`), więc tego nie wyłapał.

**Nice-to-have**:
3. Brak testu dla `data: {}` (pusty projekt w Orchestratorze — ścieżka istnieje, asercji
   nie ma).
4. Test `test_wrapper_aliasow_4xx_rzuca_wyjatek_do_gory` nie weryfikuje, że `log(...)`
   został zawołany — mutacja `log(...) → pass` by przeszła.
5. TTL 600 s w aucie: zmiana aliasu = do 10 min opóźnienia. Dla aliasów edytowanych
   w dniach (zasadnie), ale potencjał na „zmieniłem i nie działa" — ETag albo
   `POST /api/aliases/invalidate` to osobne zadanie.

**Potwierdzenia**:
- ZASADY 5.9: 4xx **faktycznie** rzuca (`raise`), nie cichy fallback — kod zgodny
  z komentarzem i testem.
- `BaseException` (KeyboardInterrupt, SystemExit) **nie** jest łapany przez
  `except Exception` — przechodzi dalej.
- Mock `urllib.error.HTTPError` w teście matchuje prawdziwe zachowanie `api()`.

### Z26 — fix KRYT 2 z Z25 code review 2 (noc 2026-10-13)

Profesor zlecił w petli: `outcome="timeout"` dla `rc != 0` bez TimeoutExpired → naprawić
na `outcome="error"`, enum spec rozszerzony, pytest z mutacją (ZASADY 4.4 druga połowa).

**Miary (ZASADY 1.2 liczby):**
- Przed: 98 pytest passed, `outcome="timeout"` dla rc=1 (fałszywy, z Z25 pomiarem live)
- Po: 99 pytest passed (+1 nowy test), `outcome="error"` dla rc=1 + pole `rc` w response
- Mutacja ręczna `"error"` → `"timeout"` w kodzie: test padł z `E - error / E + timeout`,
  cofnięcie zrobione, `git diff` czyste.

**Zakres zmian** (zgodnie z profesorem — tylko 3 miejsca):
1. Kod `_car_stop` w `voice_gateway.py`: rozdzielone `except TimeoutExpired` (zwraca 200
   z `outcome="timeout"`) od `rc != 0` bez timeoutu (`outcome="error"` + `rc` field).
2. Spec `car-window-dispatch/spec.md` enum rozszerzony: `sent | resolved | ambiguous |
   missing | refused | error | timeout` z notą, że `error` = błąd systemowy bez timeoutu.
3. Nowy pytest `test_stop_rc_nonzero_zwraca_outcome_error_nie_timeout` używający
   `monkeypatch` na `subprocess.run` → zwraca FakeResult z `returncode=1`. Asertuje:
   `outcome == "error"`, `outcome != "timeout"`, `rc == 1`.

**Mutacja uzyta jako warunek akceptacji**: zamiana `"outcome": "error"` → `"outcome":
"timeout"` w `else` branch. Pytest wyjście: `FAILED tools/tests/test_car_dispatch.py::
test_stop_rc_nonzero_zwraca_outcome_error_nie_timeout`. Komunikat asercji: `rc=1 bez
timeoutu zwraca outcome='timeout', oczekiwano 'error' (Z26 KRYT 2)`.

**Semantyka różnicowo**: dla user `error` = coś poszło nie tak po stronie bramki /
tmux (można spróbować ponownie); `timeout` = czas wygasł (warto zwiększyć budżet albo
sprawdzić obciążenie). Rozróżnienie było niemożliwe przed Z26.

**ZASADY 5.9 (korekta w tej samej sesji)**: KRYT 2 wykryte w Z25, naprawione w Z26
tej samej nocy. Nie zostawiamy do „jutra".

### Audyt pokrycia OpenSpec (Z22)

Inwentaryzacja z `voice_gateway.py` (grep na `path == "/api/car/"`): **znaleziono 12 endpointów**
(zgodnie z planem). OpenSpec changes dotykające `/api/car/`: **1** (`carplay-okna-projektow`).

| endpoint | handler | zmiana OpenSpec | pokrycie | notatka |
|---|---|---|---|---|
| GET /api/car/status | `_car_status` | carplay-okna-projektow | pełne | spec „Rozszerzone endpointy" + task 2a.1 + 2 scenariusze |
| POST /api/car/open | `_car_open` | carplay-okna-projektow | pełne | spec + task 2a.2 + scenariusz „Open idempotentny" |
| GET /api/car/project/<name>/summary | `_car_project_summary` | carplay-okna-projektow | pełne | spec + task 2a.3 + scenariusz „Token-match" |
| POST /api/car/dispatch | `_car_dispatch` | carplay-okna-projektow | pełne | spec „Endpoint HTTP dyspozytora" + tasks 2.1–2.8 + 4 scenariusze |
| POST /api/car/todo | `_car_todo` | carplay-okna-projektow | pełne | spec „Endpointy wsparcia głosowego" + task 2b.1 |
| POST /api/car/zamknij | `_car_zamknij` | carplay-okna-projektow | pełne | spec + task 2b.2 + 2 scenariusze (kasuje, idempotentny) |
| POST /api/car/powtorz | `_car_powtorz` | carplay-okna-projektow | pełne | spec + task 2b.3 + scenariusz „Dispatch zapisuje last_text" |
| GET /api/car/ostatnie_todo | `_car_ostatnie_todo` | carplay-okna-projektow | pełne | spec + task 2c.1 + scenariusz „Ostatnie TODO n=3" |
| GET /api/car/projekty | `_car_projekty` | carplay-okna-projektow | pełne | spec „Endpointy użyteczne" + task 2c.6 + scenariusz |
| GET /api/car/metryki | `_car_metryki` | carplay-okna-projektow | pełne | spec „Endpointy użyteczne" + task 2c.7 + scenariusz „Metryki top-3" |
| GET /api/car/test-audio | branch w `do_GET` | carplay-okna-projektow | pełne | spec „Diagnostyczny" + tasks 1.1, 1.2, 7.1 (usunięcie) |
| GET /api/car/test-text | branch w `do_GET` | carplay-okna-projektow | pełne | spec + task 7.1 (usunięcie po PoC) |

**Rozkład**: **12 pełne / 0 częściowe / 0 brak**.

**Historia**: `/api/car/command` (oryginalny PoC) **zastąpiony przez `/api/car/dispatch`** w D10
design.md po pomiarze 2026-10-12 (Siri Shortcut odrzucony, HA Assist zastępuje). W proposal.md
i design.md zostaje jako dziedzictwo — nie liczymy jako „produkcyjny" endpoint.

**Wniosek**: wszystkie 12 produkcyjnych endpointów ma pełne pokrycie OpenSpec (proposal → design
→ spec → tasks). Nie trzeba zakładać nowej zmiany dla samej dokumentacji — `carplay-okna-projektow`
pokrywa cały zestaw.

### Rozdzielczość w logu bramki (serie 20:15–20:22 wieczór)

- STT widzi `Klon/Klok/Klot/Klod` — dodane do wariantów wyzwalaczy
- `Claude Pomoc` dopasowany 0.71 (OK)
- `Klot do okna project integration` → `turn_on project_integration` 0.83
  (ZAADRESOWANE przez przemianowanie encji w entity_registry)
- `Klod otwórz okno HA` dopasowany 0.93 (OK)
- `jaka godzina` → HA odpowiada „22:21"
