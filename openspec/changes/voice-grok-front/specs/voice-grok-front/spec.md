## ADDED Requirements

### Requirement: Front glosowy nie zawiera mozgu
Serwer MCP SHALL przekazywac kazde pytanie i kazde zlecenie do orchestratora
(`POST /api/agent/chat`) i SHALL NOT zawierac wlasnego promptu systemowego, wlasnego wywolania
modelu ani wlasnej listy repozytoriow. Kazda decyzja „o co chodzi kierowcy" SHALL zapadac po
stronie orchestratora.

#### Scenario: Pytanie o stan projektu
- **WHEN** klient glosowy wola narzedzie `ask` z wypowiedzia „co slychac w projekcie HA"
- **THEN** serwer wysyla ja do orchestratora bez modyfikacji tresci i nie wola modelu samodzielnie

#### Scenario: Proba obejscia orchestratora
- **WHEN** w kodzie serwera pojawia sie wywolanie `claude` albo wlasna lista sciezek repozytoriow
- **THEN** test tej zmiany SHALL to wykryc i SHALL padac

### Requirement: Rozmowa przezywa timeout klienta glosowego
Serwer SHALL rozdzielic zadanie od odbioru odpowiedzi na dwa narzedzia: `ask` SHALL wracac
natychmiast ze statusem `working`, a `get_reply` SHALL byc odpytywane wielokrotnie az do statusu
`done`. Opis narzedzia `get_reply` SHALL wprost instruowac klienta, zeby wolal je ponownie,
dopoki status to `working`.

#### Scenario: Odpowiedz dluzsza niz timeout klienta
- **WHEN** orchestrator odpowiada po 30 s, a klient zrywa polaczenie po 20 s
- **THEN** `ask` oddalo `working` przed zerwaniem, a kolejne `get_reply` oddaje pelna odpowiedz

#### Scenario: Zadanie jeszcze trwa
- **WHEN** `get_reply` trafia na niezakonczone zadanie
- **THEN** odpowiedz ma status `working`, a nie pusty tekst ani blad

### Requirement: Kontekst rozmowy trzyma serwer
Serwer SHALL przechowywac n ostatnich par (pytanie, odpowiedz) na identyfikator sesji i SHALL
dolaczac je do kolejnego zapytania. Liczba przechowywanych par SHALL byc parametrem konfiguracji,
a jej wartosc SHALL zostac wybrana pomiarem, nie zalozeniem.

#### Scenario: Odwolanie do poprzedniej tury
- **WHEN** kierowca pyta „a co z tym drugim projektem" zaraz po pytaniu o dwa projekty
- **THEN** zapytanie wyslane do orchestratora zawiera poprzednia ture

#### Scenario: Nowa sesja
- **WHEN** klient podaje identyfikator sesji, ktorego serwer nie zna
- **THEN** rozmowa zaczyna sie bez historii, a serwer nie miesza jej z zadna inna sesja

### Requirement: Sciezka zapasowa bez MCP
Serwer SHALL wystawiac endpointy `/voice/ask` i `/voice/reply` przyjmujace token w sciezce albo
w parametrze zapytania, tak aby dzialaly ze Skrotow iOS, ktore nie ustawiaja naglowkow HTTP.

#### Scenario: Klient glosowy bez MCP
- **WHEN** klient nie potrafi wolac konektora MCP w trybie glosowym
- **THEN** ten sam przebieg rozmowy jest osiagalny przez `/voice/ask` i `/voice/reply`

### Requirement: Publiczne wystawienie ma domyslnie tylko odczyt
Gdy serwer jest wystawiony publicznie (Tailscale Funnel), narzedzia zapisujace SHALL byc domyslnie
wylaczone. Wlaczone SHALL dzialac wylacznie przez istniejaca sciezke wykonawcza z jej bramkami
(czyste drzewo, testy, zero usuniec, limit plikow) i SHALL wymagac potwierdzenia glosem przed
wykonaniem. Serwer SHALL logowac kazde wywolanie i SHALL ograniczac tempo.

#### Scenario: Zlecenie bez wlaczonego zapisu
- **WHEN** kierowca prosi o zmiane w kodzie, a zapis jest wylaczony
- **THEN** serwer odmawia zdaniem po polsku nadajacym sie do przeczytania na glos, a nie kodem bledu

#### Scenario: Zlecenie z wlaczonym zapisem
- **WHEN** zapis jest wlaczony i kierowca potwierdzil glosem
- **THEN** zlecenie idzie przez `execute_worker`, a jego bramki SHALL NOT byc omijane

### Requirement: O cudzych oknach mozna tylko powiedziec
Serwer SHALL udostepniac odczyt stanu otwartych sesji Claude Code na maszynie (repozytorium,
zajete czy bezczynne) i SHALL NOT wysylac do nich polecen.

#### Scenario: Pytanie o stan pracy
- **WHEN** kierowca pyta „co jest teraz otwarte na pececie"
- **THEN** odpowiedz wymienia repozytoria i stan (zajete / bezczynne) z `claude agents --json`

#### Scenario: Proba wejscia w zajete okno
- **WHEN** kierowca prosi, zeby cos dopisac w otwartym, zajetym oknie
- **THEN** serwer odmawia i mowi, ze okno jest zajete, zamiast forkowac druga sesje w tym repo
