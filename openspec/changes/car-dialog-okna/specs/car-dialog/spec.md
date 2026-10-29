## ADDED Requirements

### Requirement: Jeden punkt wejścia dialogu

Bramka SHALL wystawiać `POST /api/car/say` z JSON `{session_id, text}` i nagłówkiem `Authorization: Bearer`.
Odpowiedź SHALL mieć postać `{text, outcome, state}`, gdzie `outcome` ∈ `answered` | `moved` | `where` |
`pending` | `queued` | `refused` | `missing` | `error` i `state` = `{mode, project?, machine?}`. Pole `text`
SHALL mieć najwyżej dwa zdania i zawierać polskie znaki diakrytyczne.

#### Scenario: Wypowiedź bez komendy w trybie głównym
- **WHEN** `state.mode = main` i `text = "ile jest dziś zadań otwartych"`
- **THEN** odpowiedź pochodzi ze ścieżki rozmowy głównej, `outcome = answered`, `state.mode = main`

#### Scenario: Odmowa przed rozstrzygnięciem
- **WHEN** `text` zawiera wzorzec z `CAR_REFUSE_PATTERNS`
- **THEN** `outcome = refused`, stan bez zmian, nic nie trafia do okna

### Requirement: Przejście do okna projektu

Wypowiedź zaczynająca się od `przejdź do` / `przełącz na` / `wejdź do` / `do okna` + nazwa projektu SHALL
ustawić `mode = window` z rozwiązanym projektem i maszyną. Nazwa SHALL być rozwiązana tym samym kodem co
pytania o projekty (`find_project`, aliasy, `okna.resolve`). Dwa i więcej trafień SHALL dać `pending`
z pytaniem „który: A czy B?" i nic nie wysyła do okna.

#### Scenario: Projekt z jednym oknem
- **WHEN** „przejdź do projektu car integration", okno otwarte tylko na komputerze w pracy
- **THEN** `outcome = moved`, `state = {window, Car_chatGPT_integration, praca}`, bez pytania o maszynę

#### Scenario: Okno otwarte na obu maszynach
- **WHEN** „przejdź do HA", okno otwarte w pracy i w domu
- **THEN** `outcome = pending`, `text` pyta „w pracy czy w domu?", odpowiedź „w pracy" daje `moved`;
  wybór jest zapamiętany dla tego projektu do końca dnia

#### Scenario: Maszyna podana w zdaniu
- **WHEN** „przejdź do HA w domu"
- **THEN** brak pytania, `machine = dom`

#### Scenario: Okno zamknięte
- **WHEN** okno nie jest otwarte na żadnej maszynie
- **THEN** bramka otwiera je na maszynie domyślnej (praca), mówi „otwieram X w pracy", a polecenia wysłane
  przed gotowością okna czekają w kolejce

### Requirement: Polecenia w oknie idą jedno po drugim

W `mode = window` każda wypowiedź niebędąca komendą dialogu SHALL trafić do kolejki FIFO okna
`(maszyna, projekt)` jako tekst z tagiem `[glos-ha]`. Polecenie do zajętego okna SHALL zostać zapamiętane
(`outcome = queued`, „po bieżącym zadaniu"), a odpowiedź SHALL dojść asynchronicznie przez
`script.odpowiedz_asystenta`. Kolejka SHALL przeżyć restart bramki.

#### Scenario: Dwa polecenia pod rząd
- **WHEN** drugie polecenie przychodzi, zanim okno odpowiedziało na pierwsze
- **THEN** idzie do okna dopiero po odpowiedzi na pierwsze, w kolejności wypowiedzenia

#### Scenario: Zdanie zaczynające się od słowa-klucza
- **WHEN** w oknie użytkownik mówi „powiedz oknu wróć do pierwszego akapitu"
- **THEN** do okna trafia „wróć do pierwszego akapitu", stan nie zmienia się

### Requirement: Powrót i rozmowa główna z pamięcią

`wróć` / `rozmowa główna` / `wyjdź z okna` SHALL ustawić `mode = main`, a do `voice_history` dopisać wymianę
z oknem (projekt, ostatnie `Glosowo:`), tak by następne pytanie rozmowy głównej miało ten kontekst.
`wróć do poprzedniego` SHALL przejść do poprzedniego okna z `trail`.

#### Scenario: Pytanie o okno po powrocie
- **WHEN** użytkownik wraca z okna X i pyta „co tam było z X?"
- **THEN** odpowiedź korzysta z wpisu w historii głównej i `car_trail`, nie z domysłu

### Requirement: Gdzie jestem

Wypowiedź „gdzie jestem" / „gdzie pracujemy" SHALL w każdym stanie zwrócić odpowiedź `outcome = where`
złożoną ze zmierzonych pól: tryb, projekt, maszyna, czy okno pracuje (i od jak dawna), liczba poleceń w kolejce.
Brak danych SHALL być wymieniony wprost.

#### Scenario: W oknie, które pracuje
- **WHEN** `mode = window` i monitor pokazuje `state = working`, zadanie od 4 minut
- **THEN** odpowiedź zawiera nazwę projektu, maszynę i „pracuje od 4 minut"

#### Scenario: Brak stanu okna
- **WHEN** monitor nie zwraca rekordu okna
- **THEN** odpowiedź mówi, że stanu okna nie widać; liczby nie są zgadywane

### Requirement: Pytanie o projekty tak samo w aucie i w domu

Pytanie o projekty, maszyny, zadania lub obliczenia (`voice_brief.wants_status`) SHALL być obsłużone tym samym
kodem w aucie i w domu, w każdym stanie dialogu, i SHALL zwracać zmierzony stan z monitora.

#### Scenario: To samo pytanie, dwa wejścia
- **WHEN** „jakie projekty teraz pracują" przez `/api/car/say` i przez `/voice/ask-text`
- **THEN** oba teksty zawierają ten sam zestaw projektów ze stanem `working`

### Requirement: Stan nie wygasa po cichu

Stan dialogu SHALL być trzymany co najmniej 4 godziny ciszy. Pierwsza komenda po przerwie dłuższej niż
10 minut SHALL zacząć odpowiedź od informacji, gdzie użytkownik jest.

#### Scenario: Powrót po 30 minutach
- **WHEN** użytkownik był w oknie X, 30 minut ciszy, mówi „dodaj test do parsera"
- **THEN** polecenie idzie do okna X, a odpowiedź zaczyna się od „Jesteś nadal w oknie X."
