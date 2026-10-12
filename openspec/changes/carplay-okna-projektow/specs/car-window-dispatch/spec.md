## ADDED Requirements

### Requirement: Endpoint HTTP dyspozytora dla HA Assist

Bramka głosowa (`project_integration/tools/voice_gateway.py`) SHALL wystawiać endpoint
`POST /api/car/dispatch` dostępny tylko w tailnecie z TLS, akceptujący **JSON**
`{session_id, project, prompt}` (`Content-Type: application/json`) i nagłówek
`Authorization: Bearer <token>` (token wspólny z HA `rest_command_claude.yaml`).
Odpowiedź SHALL mieć `Content-Type: application/json` z ciałem JSON
`{text, outcome, resolved_project?}`, gdzie `outcome` ∈
`sent` | `resolved` | `ambiguous` | `missing` | `refused` | `timeout`. **STT i TTS
nie są odpowiedzialnością bramki** — robi je pipeline HA, bramka tylko dyspozytor
tekst → tmux → tekst.

#### Scenariusz: Pomyślny dispatch z HA

- **WHEN** HA wysyła POST z JSONem `{"session_id":"ha-conv-1","project":"Car_chatGPT_integration","prompt":"dodaj test do parsera"}`
  i prawidłowym tokenem
- **THEN** bramka woła `okna.resolve("Car_chatGPT_integration")` → jeden projekt (sanity),
  `tmux send-keys` dostarcza tekst do sesji, `tmux capture-pane` łowi pierwszą linię `Glosowo:`,
  bramka zwraca JSON `{"text":"<tekst po Glosowo: bez prefiksu>","outcome":"sent","resolved_project":"Car_chatGPT_integration"}`

#### Scenariusz: Odmowa bez tokenu

- **WHEN** klient wysyła POST bez `Authorization: Bearer`
- **THEN** bramka zwraca `401` bez body JSON, nic nie wysyła do tmux

### Requirement: Rozszerzone endpointy funkcjonalne dla HA Assist (status, open, project summary)

Bramka SHALL wystawiać dodatkowe endpointy dla komend głosowych HA Assist (poza
`/api/car/dispatch`):

- `GET /api/car/status` — bez body; agreguje `/api/state` Monitor, zwraca JSON
  `{text, outcome, working, tasks_open, total_projects}`. Pole `text` jest krótkie,
  Głosowo-friendly: „projektow N, pracuje X nad Y, zadan otwartych M, niewypchnietych K".
- `POST /api/car/open` — body JSON `{project}`; wywołuje `tools/okno.py <project>` jako
  subprocess, zwraca `{text, outcome, resolved_project, raw}`. Idempotentne — zwraca
  „okno X juz dziala" gdy już istnieje.
- `GET /api/car/project/<name>/summary` — nazwa URL-encoded w ścieżce; agreguje rekord
  repo z `/api/state`, zwraca `{text, outcome, resolved_project, state, done, total}`.
  Fuzzy match przez `okna.resolve`.

Wszystkie trzy MUST wymagać `Authorization: Bearer <token>` z `~/.claude/car_tokens.json`;
odmowa 401. Resolve nazw projektów MUST reuse `okna.resolve` (identyczny mechanizm fuzzy
jak w `/api/car/dispatch`).

#### Scenariusz: Status zwraca liczby i aktywnego

- **WHEN** HA GET `/api/car/status` z poprawnym tokenem, Monitor zwraca stan 3 projektów
  pracujących z 22 wszystkich, 182 zadania otwarte
- **THEN** bramka zwraca `{"text": "projektow 22, pracuje <pierwszy> nad <label>, plus 2 innych,
  zadan otwartych 182, ...", "outcome": "sent", "working": ["X","Y","Z"], "tasks_open": 182,
  "total_projects": 22}`

#### Scenariusz: Open idempotentny

- **WHEN** HA POST `/api/car/open` dwukrotnie z `{"project": "voice"}`
- **THEN** pierwsze wywołanie zwraca `{"text": "otwieram voice", "outcome": "sent", "raw":
  "voice: otwarty na monitorze N w grupie"}`; drugie zwraca `{"text": "okno voice juz dziala",
  "outcome": "sent", "raw": "voice: aktywny"}`

#### Scenariusz: Project summary token-match dla "car integration"

- **WHEN** HA GET `/api/car/project/car%20integration/summary` (fuzzy, dwa tokeny
  rozproszone w nazwie `Car_chatGPT_integration`)
- **THEN** `okna.resolve` 4-ty tier (token-match) rozwiązuje jednoznacznie do
  `Car_chatGPT_integration`, bramka zwraca `{"text": "Car_chatGPT_integration, pracuje nad X,
  zadan N z M otwartych.", "resolved_project": "Car_chatGPT_integration", ...}`

### Requirement: Endpointy wsparcia głosowego (todo, zamknij, powtorz, ostatnie_todo)

Bramka SHALL wystawiać dodatkowe endpointy dla wygody użytkownika głosowego:

- `POST /api/car/todo` — body JSON `{text, project?, session_id?}`; zapisuje linię do
  `~/.claude/carplay_todos.jsonl` (poza repo). Project auto z sticky session jeśli puste.
- `POST /api/car/zamknij` — body JSON `{session_id}`; kasuje wpis sticky session, zwraca
  „zamkniete, bylo X" lub „nie bylo aktywnej sesji".
- `POST /api/car/powtorz` — body JSON `{session_id}`; zwraca `last_text` zapisany po
  ostatnim pomyślnym dispatchu dla tej sesji (albo „nie mam co powtorzyc").
- `GET /api/car/ostatnie_todo?n=5` — czyta końcówkę `carplay_todos.jsonl`, buduje tekst
  typu „ostatnie zadania: X; Y; Z"; `n` od 1 do 10.

Wszystkie te 4 endpointy MUST wymagać `Authorization: Bearer <token>`; MUST zwracać JSON
z `{text, outcome}` gdzie `outcome` ∈ `sent | missing`. **Rejestr sesji** MUST być
zabezpieczony `threading.Lock` wokół sekwencji read-modify-write (`car_set_active`,
`car_update_last_text`, `_car_zamknij`) — bez tego dwa równoległe dispatchy nadpiszą się
nawzajem.

#### Scenariusz: Dispatch zapisuje last_text

- **WHEN** HA woła `/api/car/dispatch` z `{session_id: "s1", ...}`, bramka łowi
  `Glosowo: zrobione`
- **THEN** `car_update_last_text("s1", "zrobione")` zapisuje do rejestru;
  kolejne `/api/car/powtorz` z tym `session_id` zwraca `{"text": "zrobione", "outcome": "sent"}`

#### Scenariusz: Zamknij kasuje sticky

- **WHEN** sesja `s1` ma projekt `X` w rejestrze, HA woła `POST /api/car/zamknij`
  z `{session_id: "s1"}`
- **THEN** bramka zwraca `{"text": "zamkniete, bylo X", "outcome": "sent"}`;
  następny dispatch bez pola `project` i bez prefiksu zwraca `{"outcome": "missing",
  "text": "sesja wygasla, powiedz do okna X"}`

#### Scenariusz: Zamknij idempotentny

- **WHEN** sesja `s1` nie ma wpisu w rejestrze, HA woła `POST /api/car/zamknij`
- **THEN** bramka zwraca `{"text": "nie bylo aktywnej sesji", "outcome": "sent"}`,
  bez błędu

#### Scenariusz: Ostatnie TODO n=3

- **WHEN** `carplay_todos.jsonl` ma 5 wpisów, HA woła `GET /api/car/ostatnie_todo?n=3`
- **THEN** bramka zwraca `{"text": "ostatnie zadania: X; Y; Z", "outcome": "sent", "items": [...]}`
  gdzie X, Y, Z to teksty z ostatnich 3 wpisów (najstarszy pierwszy w tekście)

### Requirement: Rozszerzony parser `okna.resolve` o token-match

`okna.resolve(query, names)` SHALL próbować kolejno 4 tiers: (1) exact match normalized,
(2) prefix match normalized, (3) substring match normalized, (4) **token-match**:
query dzielone na tokeny po znakach niealfanumerycznych; gdy ≥ 2 tokeny, pasuje nazwa
w której każdy token jest podciągiem znormalizowanej nazwy. Pierwszy niepusty tier wygrywa.

#### Scenariusz: Token-match dla rozstrzelonej nazwy

- **WHEN** `okna.resolve("car integration", ["Car_chatGPT_integration", "HA"])`
- **THEN** zwraca `["Car_chatGPT_integration"]` (token-match: „car" ⊂ „carchatgptintegration" oraz
  „integration" ⊂ „carchatgptintegration"); exact/prefix/substring puste

### Requirement: Diagnostyczny endpoint audio dla PoC Siri (do usunięcia)

Bramka SHALL wystawiać `GET /api/car/test-audio` oraz `GET /api/car/test-text` jako
narzędzia diagnostyczne do pomiaru warstwy transportu Tailscale → CarPlay (zanim
dowiedliśmy, że Siri Shortcut nie dociąga audio). Oba endpointy MUST być usunięte
po zakończeniu zmiany (task 7.1).

#### Scenariusz: Test audio zwraca ten sam dźwięk co preview

- **WHEN** klient `GET /api/car/test-audio`
- **THEN** bramka zwraca `audio/wav` lub `audio/mpeg` z tekstem `test głosu w aucie`
  wymówionym przez `speak()` (tego samego głosu co `/voice/preview`)

#### Scenariusz: Test text zwraca tekst do syntezy Siri Shortcutem

- **WHEN** klient `GET /api/car/test-text`
- **THEN** bramka zwraca `text/plain; charset=utf-8` z ciałem `test głosu w aucie`

### Requirement: Fuzzy match nazwy projektu wymaga jednoznacznosci

Bramka SHALL użyć `project_integration/tools/okna.py:resolve()` do rozwiązania nazwy projektu
z transkrypcji. Dispatch do `tmux send-keys` MUST NOT nastąpić, dopóki rozwiązanie nie wskaże
dokładnie **jednego** projektu z mapy `~/.claude/monitor_repos.env`.

#### Scenariusz: Dwuznacznosc skutkuje pytaniem

- **WHEN** użytkownik mówi „projekt car", a `okna.resolve("car")` zwraca
  `["Car_chatGPT_integration", "Car_history"]`
- **THEN** bramka NIE wywołuje `send-keys`, odpowiedź to `audio/mpeg` z `Glosowo: który projekt
  — Car chatGPT Integration czy Car history?`, `X-Dispatch-Outcome: ambiguous`, aktywna sesja
  CarPlay zostaje `pending resolution`

#### Scenariusz: Brak projektu konczy sie informacja

- **WHEN** użytkownik mówi „projekt panda, zrób X", `okna.resolve("panda")` zwraca listę pustą
- **THEN** bramka NIE wywołuje `send-keys`, odpowiedź to `Glosowo: nie znam projektu panda`,
  `X-Dispatch-Outcome: missing`, zapis w `project_files/run_files/carplay_misses.jsonl`
  z transkrypcją, kandydatami zbliżonymi i czasem

### Requirement: Rejestr aktywnej sesji CarPlay

Bramka SHALL utrzymywać plik `~/.claude/carplay_sessions.json` z sekcją per `X-Session-Id`:
`{"project": "<nazwa>", "ts": <unix>, "state": "active" | "pending" | "expired"}`. Odczyt
i zapis MUST być pod lockiem (`project_integration/monitor/lockutil.py`). Wpis SHALL wygasać
po **600 sekundach** ciszy; wpis `pending` SHALL trwać do pierwszego kolejnego POST z tym
session_id.

#### Scenariusz: Druga komenda bez prefiksu idzie do aktywnej sesji

- **WHEN** klient `S1` wysłał w ciągu ostatnich 600 s „projekt car integration: dodaj test"
  (sesja aktywna, projekt `Car_chatGPT_integration`), teraz wysyła „popraw ten test o nazwę
  pliku"
- **THEN** bramka pomija parser projektu, wywołuje `send-keys` do sesji
  `Car_chatGPT_integration` z całym tekstem, odnawia timestamp sesji

#### Scenariusz: Wygasnięcie sesji wymusza wybor projektu

- **WHEN** klient `S1` ostatnio aktywny 601 s temu wysyła „zrób X" bez prefiksu
- **THEN** bramka NIE wywołuje `send-keys`, odpowiedź `Glosowo: sesja wygasła, powiedz
  projekt X`, `X-Dispatch-Outcome: missing`, wpis sesji usunięty

### Requirement: Rozpoznawanie fraz po stronie HA (nie bramki)

Parser nazw projektu i oddzielania ich od reszty promptu SHALL żyć w konfiguracji HA
(`voice/claude_sentences_pl.yaml` + `voice/claude_aliases.yaml`), nie w kodzie bramki.
Bramka otrzymuje już **sparsowane** pola `project` i `prompt` w JSONie. Powód (D10):
Speech-to-Phrase w HA potrzebuje słownika z góry — fuzzy match po STT nie ma sensu.

#### Scenariusz: Alias HA rozwiązuje się do projektu

- **WHEN** HA woła `POST /api/car/dispatch` z `{"project":"car integration","prompt":"dodaj test"}`
- **THEN** bramka woła `okna.resolve("car integration")` jako sanity check — zwraca
  `Car_chatGPT_integration`, dispatchuje tam

#### Scenariusz: Alias nieznany bramce

- **WHEN** HA woła z `{"project":"panda","prompt":"X"}` (błąd w `claude_aliases.yaml`
  albo wymawialna nazwa nie zdążyła dostać się do mapy)
- **THEN** bramka zwraca `{"text":"nie znam projektu panda","outcome":"missing"}`;
  HA wymawia to przez TTS

### Requirement: Odmowa polecen pisujacych w aucie

Bramka SHALL odrzucić dispatch promptu zawierającego **po transkrypcji i normalizacji
spacji** jakiekolwiek z: `git push`, `git reset --hard`, `rm -rf`, `sudo `, `--force`,
`--dangerously-skip-permissions`, `drop table`, `shutdown`, `reboot`, `format `. Odmowa
MUST być zalogowana w `project_files/run_files/carplay_refusals.jsonl` z transkrypcją
i słowem, które ją spowodowało.

#### Scenariusz: Odmowa prosby o push

- **WHEN** klient wysyła „projekt car integration zrób git push na main"
- **THEN** bramka NIE wywołuje `send-keys`, odpowiedź `Glosowo: w aucie tego nie zrobię,
  zrób z telefonu`, `X-Dispatch-Outcome: refused`, zapis w `carplay_refusals.jsonl`

### Requirement: Timeout 30 sekund na `Glosowo:` z pane

Po dispatchu bramka SHALL czekać na pojawienie się linii `Glosowo:` w output pane
(`tmux capture-pane` co 500 ms, linia **nowsza** niż timestamp wysłania) maksymalnie **30**
sekund. Po przekroczeniu bramka SHALL zwrócić `Glosowo: pracuję jeszcze, zapytaj za chwilę`
z `X-Dispatch-Outcome: timeout` i oznaczyć sesję `pending`. Następny POST z tego session_id
MUST sprawdzić pane po `Glosowo:` **przed** rozpoznaniem prefiksu „projekt".

#### Scenariusz: Timeout zwraca „pracuje jeszcze"

- **WHEN** sesja Claude pisze dłużej niż 30 s po send-keys
- **THEN** bramka zwraca `audio/mpeg` z tekstem jak wyżej po dokładnie 30±1 s od końca
  dispatchu, sesja oznaczona `pending`

#### Scenariusz: Odbior opoznionej odpowiedzi w nastepnym POST

- **WHEN** sesja `pending` dostaje POST „co tam", a pane zawiera `Glosowo: zrobione, test
  dodany w test_parser.py`
- **THEN** bramka NIE wywołuje `send-keys`, zwraca audio tej linii `Glosowo:`,
  `X-Dispatch-Outcome: sent`, sesja z powrotem `active`

### Requirement: Reuse istniejących modułów `project_integration`

Implementacja MUST wywoływać istniejące funkcje bez duplikacji:
- `project_integration/tools/okna.py:parse_repos`, `okna.resolve`, `okna.tmux_name`
- `project_integration/monitor/voice_gateway.py:spoken_summary`, `speak`, kolejka TTS
- `project_integration/monitor/lockutil.py` (lock pliku rejestru)
- transport `tmux send-keys -l` i `C-m` wzorowany na
  `project_integration/monitor/cli_bridge_reap.sh:288`.

Zmiana MUST NOT definiować własnego fuzzy matchera, własnego TTS ani własnego klienta
Whispera.

#### Scenariusz: Wywolanie okna.resolve zamiast wlasnego matchera

- **WHEN** przeglad kodu nowego endpointu
- **THEN** jedyne wywołanie rozwiązujące nazwę projektu w nowym kodzie to `okna.resolve(...)`
  z `project_integration/tools/okna.py`; brak definicji funkcji zawierającej `prefix` lub
  `substring` w nowym pliku bramki

### Requirement: Kafelek HA Assist w CarPlay jako wejście do systemu

Repo `Car_chatGPT_integration` SHALL dostarczyć `notes/HANDOFF_carplay_okna.md` opisujący:
jak dodać kafelek **Assist** jako Quick Access w HA Companion → CarPlay (potwierdzone
w kuchni 2026-10-12); tabelę pomiarową serii C z liczbą prób (≥ 10), medianą czasu
„koniec mówienia → pierwsze słowo z głośnika auta", liczbą poprawnych rozpoznań nazwy
projektu, warunkami jazdy (prędkość ≥ 70 km/h w co najmniej 3 próbach). Prerejestracja
MUST istnieć **przed** jazdą (`openspec/changes/carplay-okna-projektow/tasks.md`, sekcja
6), zgodnie z ZASADY 3.3.

#### Scenariusz: Prerejestracja istnieje przed pomiarem

- **WHEN** inspekcja repo w dniu rozpoczęcia jazdy pomiarowej
- **THEN** `tasks.md` ma odhaczone zadanie prerejestracji, zawiera hipotezę, liczbę testowanych
  porównań, warunek NEGATYWU i czego wynik nie uprawnia; `notes/HANDOFF_carplay_okna.md`
  nie zawiera jeszcze tabeli pomiarów serii C

### Requirement: Siri Shortcut jest wyłącznie diagnostyką (nie wejściem)

Zmiana MUST NOT dostarczać Shortcut iOS „Projekt" jako docelowego wejścia użytkownika.
Pomiar 2026-10-12 wykazał, że Siri zamyka sesję audio Shortcuta zanim `Odtwórz dźwięk`
dokończy. Istniejące Shortcuty `CarPlay audio test` i `CarPlay text test` MUST zostać
oznaczone w `notes/HANDOFF_carplay_okna.md` jako diagnostyczne (sprawdzanie Tailscale,
certyfikatu, podstawowego dociągu audio) i usunięte lub pozostawione według decyzji
użytkownika po zakończeniu zmiany.

#### Scenariusz: HANDOFF oznacza Siri jako diagnostykę

- **WHEN** inspekcja `notes/HANDOFF_carplay_okna.md` po zakończeniu zmiany
- **THEN** sekcja 1.1 (Shortcut A i B) jest podpisana „diagnostyka Tailscale/CarPlay audio"
  z adnotacją „odrzucone jako wejście 2026-10-12", a docelowe wejście w sekcji „Seria C"
  jest kafelkiem Assist w HA Companion
