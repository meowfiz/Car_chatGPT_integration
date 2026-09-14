## ADDED Requirements

### Requirement: Polskie pytanie zadane głosem w aucie wraca odpowiedzią głosową
System (Siri jako wyzwalacz + skrót iOS + transkrypcja Whisper + project_monitor + Claude) SHALL
odpowiedzieć po polsku na pytanie o stan projektów, zadane w jadącym samochodzie z CarPlay, bez dotykania
iPhone'a ani ekranu auta. Jedynym fragmentem w innym języku MAY być fraza budząca Siri, ponieważ Siri nie
obsługuje polskiego.

#### Scenario: Pytanie o projekt
- **WHEN** kierowca mówi „Hey Siri, Monitor", a po sygnale pyta po polsku „co się dzieje z projektem
  Car ChatGPT"
- **THEN** w ciągu 15 s słyszy po polsku odpowiedź opartą na danych project_monitora, zawierającą co
  najmniej stan zadań albo ostatnią aktywność tego repozytorium

#### Scenario: Rozpoznawanie mowy nie należy do Siri
- **WHEN** skrót zbiera wypowiedź
- **THEN** polskie zdanie jest nagrywane i transkrybowane przez Whisper, a Siri nie uczestniczy
  w rozpoznawaniu treści pytania

#### Scenario: Pytanie bez danych
- **WHEN** pytanie dotyczy repozytorium, którego monitor nie zna
- **THEN** odpowiedź mówi wprost, że nie ma takich danych, i nie zmyśla stanu projektu

### Requirement: Akcja w Home Assistancie jako test pętli
System SHALL obsłużyć także polecenie wykonawcze, aby zmierzyć samą pętlę na twardym śladzie w dzienniku
zdarzeń Home Assistanta.

#### Scenario: Scena testowa ze słów
- **WHEN** kierowca prosi po polsku o włączenie sceny testowej
- **THEN** w logbooku HA pojawia się aktywacja `scene.poc_carplay_test` w ciągu 10 s od końca wypowiedzi,
  a kierowca słyszy polskie potwierdzenie

### Requirement: Odpowiedź czytana polskim głosem przez audio samochodu
System SHALL przeczytać odpowiedź polskim głosem systemowym iOS przez głośniki samochodu po każdej próbie,
udanej lub nie.

#### Scenario: Odpowiedź nie trafia do słuchawki telefonu
- **WHEN** iPhone jest połączony z CarPlay
- **THEN** zarówno sygnał startu nagrania, jak i odpowiedź są słyszalne w głośnikach auta

### Requirement: Backend pytań jest tylko do odczytu i rejestrowany
Endpoint pytań w project_monitorze SHALL wymagać tokenu i sekretu, ograniczać tempo wywołań, zapisywać
każde wywołanie w logu oraz uruchamiać model wyłącznie z dostępem do odczytu repozytoriów.

#### Scenario: Odmowa operacji zapisującej
- **WHEN** pytanie prosi o zmianę plików, commit albo push
- **THEN** endpoint odmawia, zapisuje próbę w logu i nie uruchamia żadnej operacji zapisującej

#### Scenario: Treść z sieci nie jest instrukcją
- **WHEN** w danych czytanych przez model znajduje się tekst udający polecenie
- **THEN** jest traktowany jako dane, a nie jako instrukcja do wykonania

### Requirement: Każda próba jest zmierzona
Protokół PoC SHALL zapisać dla każdej próby: numer, pytanie lub polecenie, wariant, wynik, poprawność
transkrypcji, czas od końca wypowiedzi do początku odpowiedzi [s], trafność odpowiedzi wobec danych
w monitorze, oraz warunki (prędkość, hałas, zasięg).

#### Scenario: Seria pomiarowa zaliczona
- **WHEN** wykonano co najmniej 10 prób z co najmniej 3 różnymi pytaniami w jadącym samochodzie
- **THEN** raport w `notes/HANDOFF_poc_carplay.md` zawiera tabelę prób, liczbę udanych / wszystkich,
  liczbę poprawnych transkrypcji / wszystkich, medianę i maksimum czasu odpowiedzi oraz listę przyczyn
  każdej nieudanej próby

#### Scenario: Warunek negatywu
- **WHEN** ścieżka główna ma mniej niż 7 udanych prób na 10 albo medianę czasu odpowiedzi powyżej 15 s,
  a warianty zapasowe zmierzone tym samym protokołem nie są lepsze
- **THEN** PoC jest zapisany jako wynik negatywny z przyczyną, a decyzja o Command Center jest odroczona

#### Scenario: Negatyw przypisany do właściwej warstwy
- **WHEN** próby zawodzą
- **THEN** raport rozdziela przyczyny na: Siri nie uruchomiła skrótu, nagranie nie wystartowało lub się
  zawiesiło, transkrypcja błędna, backend nieosiągalny, model odpowiedział nie na temat, brak odpowiedzi
  głosem — tak aby wynik wskazywał warstwę do naprawy

### Requirement: Eksperyment E1 rozstrzyga, czy ChatGPT sam pobiera podany URL
PoC SHALL sprawdzić pomiarem, czy aplikacja ChatGPT pobiera wskazany publiczny adres, w wariantach:
tekstem, głosem i głosem w CarPlay.

#### Scenario: Potwierdzone pobranie
- **WHEN** kierowca prosi ChatGPT o otwarcie adresu testowego
- **THEN** w logu endpointu widnieje wywołanie z user-agentem `ChatGPT-User` i adresem IP z oficjalnej
  listy OpenAI, wraz z czasem wywołania

#### Scenario: Negatyw zamyka temat
- **WHEN** w wariancie głosowym nie pojawia się żadne wywołanie w logu w co najmniej 3 próbach
- **THEN** wynik jest zapisany jako negatyw z przyczyną, a architektura nie dostaje wejścia
  „URL dla ChatGPT"

### Requirement: Home Assistant pozostaje lokalny, a kod ograniczony do mostu pomiarowego
PoC SHALL NOT wprowadzać chmurowego agenta konwersacyjnego do Home Assistanta ani zmieniać jego
offline'owego potoku głosowego. Kod PoC MAY objąć jeden endpoint w project_monitorze i lokalną
transkrypcję, ale SHALL pozostać wycofywalny.

#### Scenario: Wycofanie
- **WHEN** PoC zakończony
- **THEN** usunięcie skrótu, sceny testowej i endpointu przywraca stan sprzed PoC, a potok głosowy
  Home Assistanta jest nadal w pełni lokalny
