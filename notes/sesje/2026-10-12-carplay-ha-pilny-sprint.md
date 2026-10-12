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

### Rozdzielczość w logu bramki (serie 20:15–20:22 wieczór)

- STT widzi `Klon/Klok/Klot/Klod` — dodane do wariantów wyzwalaczy
- `Claude Pomoc` dopasowany 0.71 (OK)
- `Klot do okna project integration` → `turn_on project_integration` 0.83
  (ZAADRESOWANE przez przemianowanie encji w entity_registry)
- `Klod otwórz okno HA` dopasowany 0.93 (OK)
- `jaka godzina` → HA odpowiada „22:21"
