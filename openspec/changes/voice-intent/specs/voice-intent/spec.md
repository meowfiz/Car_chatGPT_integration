## ADDED Requirements

### Requirement: Wypowiedz kierowcy zamienia sie w strukture intencji
Most SHALL zamienic transkrypcje swobodnej polskiej wypowiedzi na strukture
`{v, intent, repo, text, limit_zdan}` w wersji 1, zanim cokolwiek trafi do modelu. Zamiana SHALL
byc deterministyczna i SHALL NOT wymagac dodatkowego wywolania modelu jezykowego.

#### Scenario: Pytanie o projekt
- **WHEN** kierowca mowi „ile zadan zostalo w projekcie Car ChatGPT i co jest nastepne"
- **THEN** struktura ma `intent` rowny `ask`, `repo` rowny `Car_chatGPT_integration`, a `text`
  zawiera cala wypowiedz

#### Scenario: Limit zdan podany glosem
- **WHEN** wypowiedz zawiera „w dwoch zdaniach" (albo „w 2 zdaniach")
- **THEN** `limit_zdan` wynosi 2, a instrukcja o dlugosci odpowiedzi trafia do promptu

#### Scenario: Brak podanej dlugosci
- **WHEN** kierowca nie mowi o liczbie zdan, mowi za to „krotko"
- **THEN** `limit_zdan` jest `null`, a obowiazuje domyslny limit z promptu kierowcy

### Requirement: Nazwa repozytorium jest rozpoznawana z przekreconej mowy
Most SHALL rozpoznac repozytorium po tablicy aliasow trzymanej jako **dane**, z dopasowaniem
odpornym na bledy transkrypcji. Nazwy kanoniczne SHALL pochodzic z mapy repozytoriow maszyny
(`~/.claude/monitor_repos.env`), a nie z drugiej listy w kodzie. Dodanie projektu SHALL NOT
wymagac zmiany kodu.

#### Scenario: Whisper przekrecil nazwe
- **WHEN** transkrypcja brzmi „w projekcie Carcha gpt integration" (prawdziwe wyjscie Whispera
  z logu 2026-09-14)
- **THEN** `repo` wynosi `Car_chatGPT_integration`

#### Scenario: Kierowca pyta o wszystkie projekty
- **WHEN** wypowiedz zawiera „wszystkie projekty" albo „wszystkie repozytoria"
- **THEN** `repo` wynosi `*`, a powod rozpoznania jest zapisany w logu jako wybor jawny

#### Scenario: Zadna nazwa nie pasuje
- **WHEN** w wypowiedzi nie ma nic podobnego do znanego aliasu
- **THEN** `repo` wynosi `*`, powod w logu mowi „brak dopasowania", a most SHALL NOT dopytywac
  glosem o repozytorium

#### Scenario: Alias wskazuje na nieznane repozytorium
- **WHEN** plik aliasow ma klucz, ktorego nie ma w mapie repozytoriow maszyny
- **THEN** most wypisuje to przy starcie jako ostrzezenie i SHALL NOT przerwac dzialania

### Requirement: Rozpoznane repozytorium zawezaja zakres pytania i sa nazwane w odpowiedzi
Gdy `repo` jest rozpoznane, most SHALL uruchomic model w tym jednym katalogu, bez dokladania
pozostalych repozytoriow, oraz SHALL polecic modelowi rozpoczecie odpowiedzi od nazwy tego
repozytorium. Most SHALL NOT zadawac pytania potwierdzajacego przed odpowiedzia.

#### Scenario: Zawezony zakres
- **WHEN** struktura ma `repo` rowny `HA`
- **THEN** model dostaje katalog repozytorium `HA` i zadnego `--add-dir` do pozostalych

#### Scenario: Zle trafienie slychac
- **WHEN** parser wskaze niewlasciwe repozytorium
- **THEN** kierowca slyszy nazwe tego repozytorium na poczatku odpowiedzi i wie o pomylce bez
  dodatkowego pytania

### Requirement: Intencje zapisujace sa rozpoznawane i odrzucane glosem
Most SHALL rozpoznac `note` i `queue`, SHALL NOT ich wykonac i SHALL odpowiedziec jednym zdaniem
po polsku nadajacym sie do przeczytania glosem. Odpowiedz SHALL miec kod HTTP 200, poniewaz skrot
na iPhonie czyta tresc odpowiedzi, a kod bledu skonczylby sie cisza.

#### Scenario: Prosba o notatke
- **WHEN** kierowca mowi „zanotuj, ze trzeba dokonczyc watchdoga"
- **THEN** `intent` wynosi `note`, nic nie jest zapisywane, a kierowca slyszy, ze zapisywanie
  notatek jeszcze nie dziala

#### Scenario: Prosba o odlozenie zadania
- **WHEN** kierowca mowi „dodaj zadanie: przemierzyc czas odpowiedzi"
- **THEN** `intent` wynosi `queue`, nic nie trafia do skrzynki, a kierowca slyszy odmowe z powodem
