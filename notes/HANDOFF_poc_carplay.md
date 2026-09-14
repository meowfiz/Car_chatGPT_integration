# HANDOFF — PoC „polecenie głosem w aucie → akcja w HA → odpowiedź głosem"

Punkt wejścia do tematu PoC. Stan: **konfiguracja nierozpoczęta, pomiar nierozpoczęty.**
Zmiana OpenSpec: `openspec/changes/poc-carplay-command/`. Research: `notes/research/2026-09-14-*.md`.

## Środowisko (zadanie 1.1, zebrane 2026-09-14)

| element | wartość | skutek dla PoC |
|---|---|---|
| iPhone | 17 Pro | ma Apple Intelligence; akcja Skrótów „Use Model" dostępna |
| iOS | 26.6.2 | > 26.4, więc **Assist w CarPlay (fallback B) jest dostępny** |
| Siri | **nie używana** | ścieżka główna wymaga jej włączenia; polskiego Siri nie ma, więc język Siri = angielski, a fraza budząca to „Hey Siri, Home" |
| dyktowanie iOS | działa (klawiatura) | warstwa STT ścieżki głównej jest po stronie Apple, nie HA |
| HA Core | 2026.7.4 | — |
| HA Supervisor | 2026.09.0 | — |
| HA OS | 18.1 | — |
| interfejs HA | 20260624.6 | — |
| aplikacja HA Companion (iOS) | **nieznana** | fallback B wymaga 26.4+ — do sprawdzenia w aplikacji |
| plan ChatGPT | Go | apps i MCP niedostępne; bez znaczenia dla ścieżki głównej |

## Co zastane w repo `HA` zmienia w planie

Odczytane z `D:\claude_projects\HA\handsoff.txt` i `voice/voice_data.yaml` (2026-09-14):

1. **System głosowy jest w pełni offline i to jest zapisana zasada projektu HA**: „zero cloud dla głosu
   i automatyzacji". STT to Speech-to-Phrase, TTS to Piper (głosy gosia/darkman), wake word openWakeWord
   („Okay Nabu"), satelity M5Stack Atom Echo i HA Voice PE.
   **Konflikt do rozstrzygnięcia**: agent OpenAI Conversation w Assist (grupa zadań 4) łamie tę zasadę.
   Ścieżka główna PoC (grupy 1–3) jej nie łamie — chmura Apple robi tam dyktowanie, ale HA zostaje lokalny.
2. **Speech-to-Phrase ma statyczny słownik** — do modelu wchodzą wyłącznie frazy z `sentences.yaml`,
   polskie formy odmienione nie dochodzą same. Czyli **fallback B (Assist w CarPlay) rozpozna tylko zdania
   wcześniej zadeklarowane**, a nie swobodne polecenia. Ścieżki głównej to nie dotyczy, bo tekst przychodzi
   z dyktowania Apple.
3. **Diakrytyki są obowiązkowe** — pomiar z 2026-09-14 w `voice_data.yaml`: „wlacz telewizor" bez ogonków
   daje `no_intent_match`, z ogonkami działa. To bezpośrednio dotyczy ścieżki głównej: dyktowanie `pl_PL`
   musi zwracać polskie znaki, inaczej Assist odrzuci poprawnie usłyszane polecenie. Wchodzi do protokołu
   pomiaru jako osobna kolumna.
4. **Jedno źródło prawdy dla komend**: `voice/voice_data.yaml` + generator `voice/gen_voice_sentences.py`,
   który zapisuje słownik STP i dopasowania intencji. Scena testowa i jej alias muszą przejść przez ten
   generator, nie być dopisane ręcznie w dwóch miejscach.
5. **Skrypty trzeba eksponować do Assist ręcznie** (WebSocket `homeassistant/expose_entity`).
6. `assist_satellite.start_conversation` wymaga cloud LLM i jest w tym setupie niedostępne.
7. Brak śladu po Nabu Casa — dostęp zdalny idzie przez Tailscale. **Eksperyment E1 potrzebuje publicznego
   adresu HTTPS**, więc wymaga tunelu albo hostingu na zewnątrz; do rozstrzygnięcia.

## Rozstrzygnięcia z 2026-09-14 (po doprecyzowaniu celu)

- **Cel PoC to rozmowa z project_monitorem**, nie sterowanie domem: pytanie po polsku → odpowiedź głosem
  o stanie dowolnego projektu. Scena w HA zostaje jako twardy ślad pętli.
- **Mózg: Claude** przez nowy endpoint `POST /api/ask` w project_monitorze. OpenAI API nie wchodzi.
- **Konflikt z zasadą offline repo `HA` zniknął** — mózg jest poza HA, potok głosowy HA zostaje lokalny.
- **Subskrypcja ChatGPT Go nie podłącza się do HA**: integracja OpenAI w HA to osobno płatna platforma
  API, abonament ChatGPT nie obejmuje wywołań API. Nie ma czego podpinać.
- **Siri nie rozpoznaje polskiego i nie będzie musiała**: słyszy tylko „Hey Siri, Monitor". Polskie
  zdanie nagrywa akcja `Record Audio` i przepisuje Whisper — ten sam rodzaj modelu, dzięki któremu
  ChatGPT tak dobrze zbiera polski głos.

## Otwarte decyzje

- **D-B: publiczny adres dla E1.** Tunel, VPS, czy rezygnacja z E1. Sama ścieżka główna publicznego
  adresu **nie potrzebuje**, jeśli iPhone ma w aucie aktywny Tailscale (zadanie 1.2).
- **D-C: cel sceny testowej.** Które urządzenie ma być widocznym efektem (kandydat neutralny:
  `switch.noren_socket_1`).
- **D-D: wersja aplikacji HA Companion** na iPhonie — warunek wariantu zapasowego B.
- **D-E: maszyna w tailnecie** na Whispera i `claude -p`, i czy nie usypia.

## Tabela prób (pusta do czasu pomiaru)

| nr | polecenie | wariant | wynik | transkrypcja OK | diakrytyki OK | t_akcja [s] | t_odpowiedz [s] | prędkość | uwagi |
|---|---|---|---|---|---|---|---|---|---|

## Decyzja końcowa

Do uzupełnienia po zadaniu 5.1.
