## ADDED Requirements

### Requirement: Polskie polecenie głosowe hands-free uruchamia akcję w Home Assistant
System (Siri + skrót „Home” + dyktowanie `pl_PL` + HA Companion + Home Assistant) SHALL wykonać akcję
w Home Assistant po poleceniu wypowiedzianym **po polsku** w jadącym samochodzie z CarPlay, bez dotykania
iPhone'a ani ekranu auta. Jedynym fragmentem w innym języku MAY być fraza budząca Siri, ponieważ Siri nie
obsługuje polskiego.

#### Scenario: Scena testowa ze słów po polsku
- **WHEN** kierowca mówi „Hey Siri, Home”, skrót uruchamia dyktowanie, kierowca mówi po polsku
  „włącz scenę testową”
- **THEN** w logbooku HA pojawia się aktywacja `scene.poc_carplay_test` w ciągu 10 s od końca wypowiedzi

#### Scenario: Dyktowanie działa w języku polskim
- **WHEN** skrót uruchamia akcję `Dictate Text` z locale `pl_PL`
- **THEN** tekst przekazany do Home Assistanta jest polskim zapisem wypowiedzi, z polskimi znakami,
  a nie fonetyczną transkrypcją angielską

#### Scenario: Polecenie nierozpoznane nie wykonuje nic
- **WHEN** kierowca mówi polecenie spoza zakresu pipeline'u Assist (np. „otwórz garaż”, którego nie ma)
- **THEN** HA nie wykonuje żadnej akcji, a system czyta polską odpowiedź Assist o nierozpoznaniu

### Requirement: Odpowiedź wraca po polsku przez audio samochodu
System SHALL przeczytać odpowiedź Assist **polskim głosem** przez głośniki samochodu (akcja `Speak Text`
z jawnie wybranym głosem polskim) po każdej próbie, udanej lub nie.

#### Scenario: Potwierdzenie po akcji
- **WHEN** scena została aktywowana
- **THEN** kierowca słyszy polskie potwierdzenie (treść odpowiedzi pipeline'u Assist) w ciągu 5 s od
  aktywacji, czytane głosem polskim, nie angielskim

### Requirement: Każda próba jest zmierzona
Protokół PoC SHALL zapisać dla każdej próby: numer, polecenie, wynik (OK / błąd + rodzaj), **czy
transkrypcja polska była poprawna**, czas od końca wypowiedzi do akcji w HA [s], czas od końca wypowiedzi
do początku odpowiedzi głosowej [s], warunki (prędkość jazdy w przybliżeniu, hałas, zasięg LTE/5G).

#### Scenario: Seria pomiarowa zaliczona
- **WHEN** wykonano co najmniej 10 prób z co najmniej 3 różnymi poleceniami w jadącym samochodzie
- **THEN** raport w `notes/HANDOFF_poc_carplay.md` zawiera tabelę prób, liczbę udanych / wszystkich,
  liczbę poprawnych transkrypcji / wszystkich, medianę i maksimum obu czasów, oraz listę przyczyn każdej
  nieudanej próby

#### Scenario: Warunek negatywu
- **WHEN** ścieżka główna ma mniej niż 7 udanych prób na 10 albo medianę czasu do akcji powyżej 10 s,
  a fallbacki A i B zmierzone tym samym protokołem nie są lepsze
- **THEN** PoC jest zapisany jako wynik negatywny z przyczyną, a decyzja o Command Center jest odroczona

#### Scenario: Negatyw przypisany do właściwej warstwy
- **WHEN** próby zawodzą
- **THEN** raport rozdziela przyczyny na: Siri nie uruchomiła skrótu, dyktowanie nie wystartowało,
  transkrypcja polska błędna, Assist nie zrozumiał poprawnej transkrypcji, HA nieosiągalny, brak
  odpowiedzi głosem — tak aby wynik wskazywał warstwę do naprawy, a nie „nie działa”

### Requirement: Rozmowa prowadzona jest z modelem ChatGPT, a narzędzia wykonuje Home Assistant
Drugi pipeline Assist SHALL używać agenta OpenAI Conversation jako modelu rozmowy, a skrypty Home
Assistanta SHALL być wystawione temu agentowi jako narzędzia, tak aby model sam wybierał operację na
podstawie polskiego polecenia.

#### Scenario: Model sam wybiera narzędzie
- **WHEN** kierowca mówi swobodne polecenie, którego nie ma wśród intencji wbudowanych
  (np. „zrób jasno w salonie”)
- **THEN** agent OpenAI wywołuje właściwy skrypt lub akcję HA, a odpowiedź wraca po polsku

#### Scenario: Most do Claude'a jako narzędzie
- **WHEN** kierowca prosi o zadanie wymagające pracy z kodem (np. „sprawdź, co się dzieje z projektem X”)
- **THEN** agent wywołuje `script.claude_task`, endpoint uruchamia `claude -p` z poleceniem z zamkniętej
  listy, a kierowca słyszy wynik albo potwierdzenie z zapowiedzią powiadomienia

#### Scenario: Most odrzuca polecenie spoza listy
- **WHEN** do endpointu trafia polecenie spoza zamkniętej listy operacji
- **THEN** endpoint odmawia, zapisuje próbę w logu i nie uruchamia Claude'a

### Requirement: Eksperyment E1 rozstrzyga, czy ChatGPT sam pobiera podany URL
PoC SHALL sprawdzić pomiarem, czy aplikacja ChatGPT pobiera wskazany publiczny adres, w trzech wariantach:
tekstem, głosem i głosem w CarPlay.

#### Scenario: Potwierdzone pobranie
- **WHEN** kierowca prosi ChatGPT o otwarcie adresu testowego
- **THEN** w logu endpointu widnieje wywołanie z user-agentem `ChatGPT-User` i adresu IP z oficjalnej
  listy OpenAI, wraz z czasem wywołania

#### Scenario: Negatyw zamyka wersję A
- **WHEN** w wariancie głosowym nie pojawia się żadne wywołanie w logu w co najmniej 3 próbach
- **THEN** wynik jest zapisany jako negatyw z przyczyną, a Command Center nie dostaje wejścia
  „URL dla ChatGPT”

### Requirement: Zmiany są odwracalne, a kod ograniczony do mostu pomiarowego
Ścieżka hands-free (grupy zadań 1–3) SHALL składać się wyłącznie z konfiguracji HA i jednego skrótu iOS.
Most do Claude'a (grupa 4) MAY wprowadzić jeden minimalny endpoint, ale SHALL pozostać jednoplikowy,
uruchamiany lokalnie i przeznaczony do wyrzucenia; SHALL NOT stać się Command Center przed decyzją z 5.1.

#### Scenario: Wycofanie
- **WHEN** PoC zakończony
- **THEN** usunięcie skrótu „Home”, sceny testowej i endpointu mostu przywraca stan sprzed PoC, a w repo
  nie zostaje żaden serwis utrzymywany dalej
