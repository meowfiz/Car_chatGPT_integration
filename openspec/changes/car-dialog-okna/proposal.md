## Why

Użytkownik 2026-10-29: idea pracy głosowej jest dojrzała, HA odpowiada już na pytania o projekty, a interfejs
samochodu nadal jest zbiorem osobnych komend (9 intentów HA, 8 endpointów `/api/car/*`) z jednym pamiętanym
polem „aktywny projekt". Brakuje dialogu: nie da się powiedzieć „przejdź do projektu X", zostać tam przez kilka
poleceń, zapytać „gdzie jestem" i wrócić do rozmowy głównej bez utraty wątku. Pytanie o stan projektów w aucie
odpowiada inaczej niż to samo pytanie w domu, bo auto idzie przez `/api/car/status`, a dom przez `/voice/ask-text`
z `voice_brief`.

## What Changes

- **Jeden punkt wejścia**: `POST /api/car/say {session_id, text}` -> `{text, outcome, state}` w bramce
  (`project_integration/tools/voice_gateway.py`). Bramka rozstrzyga, co to jest za wypowiedź (komenda
  dialogu, pytanie do rozmowy głównej, polecenie do okna). HA przestaje parsować intencje: jeden wildcard
  `claude {pytanie}` + `rest_command`. Stare `/api/car/*` zostają jako aliasy na czas przejścia.
- **Dialog jako maszyna stanów** per `session_id` (conversation_id HA): `main` (rozmowa główna) albo
  `window(projekt, maszyna)`, plus `pending` (pytanie zwrotne: która maszyna, który projekt).
- **Komendy**: „przejdź do X [na komputerze w pracy/w domu]", „wróć", „gdzie jestem", „jakie projekty
  pracują" (to samo źródło co w domu), „powtórz", „zamknij okno". Wszystko inne idzie tam, gdzie jestem.
- **Maszyna**: domyślnie komputer w pracy; pytanie „na którym?" tylko gdy okno jest otwarte na obu.
- **Kolejka na okno**: polecenia do jednego okna idą jedno po drugim (FIFO); zajęte okno przyjmuje
  polecenie i odpowiada, gdy dojdzie do niego (asynchronicznie przez HA `script.odpowiedz_asystenta`).
- **Kontekst**: rozmowa główna to dotychczasowa sesja `voice` + `voice_history`; okno ma własny kontekst
  (sesja Claude Code). Dziennik `car_trail.jsonl` zapisuje przejścia i ostatnie `Glosowo:` każdego okna;
  po „wróć" rozmowa główna dostaje streszczenie tego, co było w oknie.
- **Wdrożenie rozdzielone**: bramka i dialog = okno `project_integration`; HA (jeden intent, jeden
  rest_command, usunięcie zbędnych intentów) = okno `HA`; ten projekt = plan, kontrakt, test e2e, pomiar.

## Impact

- Spec: nowa zdolność `car-dialog` (ta zmiana). `car-window-dispatch` z `carplay-okna-projektow` zostaje
  jako warstwa niższa (transport do okna, odmowy, tokeny).
- Kod: `project_integration/tools/car_dialog.py` (nowy, czysty), `voice_gateway.py` (endpoint, cienko),
  `HA/voice/*`.
- Nie zmienia: STT/TTS, `should_refuse_car`, tokeny, `okna.py`, `cli_bridge`.
