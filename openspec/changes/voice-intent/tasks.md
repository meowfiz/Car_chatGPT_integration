## 1. Schemat i dane

- [x] 1.1 Schemat intencji v1 opisany w `design.md` i w specyfikacji (`intent`, `repo`, `text`, `limit_zdan`, `v`); uzasadnienie kazdego pola, w tym dlaczego `text` zostaje cala wypowiedzia
- [x] 1.2 `poc/aliases.json`: tablica aliasow jako **dane** (klucz = nazwa kanoniczna repo, wartosc = mowione warianty), z `min_ratio` i wersja pliku; dodanie projektu nie wymaga zmiany kodu
- [x] 1.3 Nazwy kanoniczne czytane z `~/.claude/monitor_repos.env` (jedno zrodlo prawdy); alias wskazujacy na nieznane repo wypisywany przy starcie jako ostrzezenie, nie ignorowany po cichu

## 2. Parser deterministyczny

- [x] 2.1 `poc/intent.py`: `normalize()` (male litery, polskie znaki na ASCII, tylko `[a-z0-9 ]`) — wspolna podstawa wszystkich porownan
- [x] 2.2 `match_repo()`: dopasowanie aliasu po n-gramach slow o dlugosci aliasu, `difflib.SequenceMatcher`, prog `min_ratio` z pliku danych; zwraca `(repo, powod)` gdzie powod to `exact` / `fuzzy` / `explicit-all` / `ambiguous` / `no-match` (dwa repo blizej niz 0,02 od siebie to nie decyzja, tylko rzut moneta -> `*`)
- [x] 2.3 `parse_limit()`: „w jednym/dwoch/trzech/czterech/pieciu zdaniach" oraz cyfry („w 2 zdaniach"); brak liczby = `None`, bez zgadywania z „krotko"
- [x] 2.4 `parse()`: slowa kluczowe intencji (`note`, `queue`), domyslnie `ask`; zwraca pelna strukture v1
- [x] 2.5 Zero dodatkowych wywolan modelu — decyzja i jej uzasadnienie w `design.md` („Rezerwa modelowa")

## 3. Wpiecie w most

- [x] 3.1 `ask_server.py` wola `intent.parse()` po transkrypcji, przed `ask_claude`
- [x] 3.2 `intent: note | queue` -> HTTP 200 z jednym zdaniem odmowy po polsku (skrot czyta tresc, nie kod bledu); wpis w logu
- [x] 3.3 Rozpoznane `repo` zaweza zakres: `claude -p` startuje w tym katalogu i nie dostaje `--add-dir` do pozostalych
- [x] 3.4 Instrukcja zakresu w prompcie: odpowiedz zaczyna sie od nazwy repozytorium (zamiast pytania potwierdzajacego); limit zdan doklejany, gdy podany
- [x] 3.5 Log zapisuje `intent`, `repo` i **powod** dopasowania (`explicit-all` vs `no-match` to dwie rozne rzeczy, inaczej nie da sie policzyc trafnosci)
- [x] 3.6 Odpowiedz `?format=json` niesie strukture intencji, zeby dalo sie mierzyc bez czytania logu

## 4. Testy nazywajace porazke (ZASADY 4.4)

- [x] 4.1 Fixture wypowiedzi `project_files/python/tests/fixtures/wypowiedzi.json` z jawnym polem `zrodlo`: `log` (prawdziwa transkrypcja Whispera) albo `syntetyczna` (napisana recznie)
- [x] 4.2 Test: prawdziwa transkrypcja „Carcha gpt integration" trafia w `Car_chatGPT_integration` — porazka, ktorej zapobiega: parser dzialajacy tylko na poprawnie wymowionych nazwach
- [x] 4.3 Test: „zanotuj..." nie jest pytaniem, a odmowa nie ma kodu bledu — porazka: cicha zamiana zapisu w pytanie
- [x] 4.4 Test: brak dopasowania daje `*` z powodem `no-match`, a „wszystkie projekty" daje `*` z powodem `explicit-all` — porazka: pomiar trafnosci liczacy nierozpoznanie jako sukces
- [x] 4.5 Test: alias spoza mapy repozytoriow jest raportowany, a parser dziala dalej
- [x] 4.6 Sprawdzenie mutacja kazdego z powyzszych (wprowadz blad z powrotem, test ma paść) i zapis wyniku w notatce sesji

## 5. Pomiar (PREREJESTRACJA przed przebiegiem, ZASADY 3.3)

- [ ] 5.1 **PREREJESTRACJA — trafnosc rozpoznania repozytorium.**
  *Hipoteza:* reguly + aliasy rozpoznaja wlasciwe repozytorium w **>= 80%** wypowiedzi, w ktorych
  projekt jest nazwany, przy odsetku falszywych trafien **<= 10%**.
  *Dane:* fixture `wypowiedzi.json`, **>= 40 wypowiedzi**, w tym >= 5 na kazde repo z mapy
  maszyny i >= 8 bez nazwanego projektu; kazda wypowiedz ma pole `zrodlo`.
  *Wykluczenia:* wypowiedzi, w ktorych czlowiek sam nie potrafi wskazac projektu, sa oznaczone
  `oczekiwane: "*"`, a nie usuwane.
  *Definicja etykiety:* trafienie = `repo` rowne `oczekiwane`; falszywe trafienie = `repo` to
  konkretne repo, a `oczekiwane` bylo inne albo `*`; uczciwe `*` nie jest trafieniem ani falszem.
  *Jedna statystyka:* odsetek trafien; druga (falszywe trafienia) jest **warunkiem bezpieczenstwa**,
  nie druga hipoteza.
  *Liczba testowanych porownan:* **1** (jeden prog `min_ratio` = 0,82 zadeklarowany z gory).
  Strojenie progu po zobaczeniu wynikow = dopasowanie do fixture i musi zostac zapisane jako takie.
  *Konfuzje do zmierzenia:* udzial wypowiedzi `zrodlo: log` w zbiorze (fixture napisany przy
  biurku jest latwiejszy niz mowa w aucie) i dlugosc aliasu (aliasy jednoslowne falszuja latwiej).
  *Warunek NEGATYWU:* trafnosc < 70% albo falszywe trafienia > 10% -> `repo` zostaje na stale `*`,
  konczymy i nie szukamy trzeciej heurystyki.
  *Czego wynik NIE uprawnia:* niczego o mowie w jadacym aucie — fixture to tekst, nie nagrania;
  liczba z prawdziwych nagran moze byc tylko gorsza.
- [ ] 5.2 **PREREJESTRACJA — czy zawezenie zakresu skraca odpowiedz.**
  *Hipoteza:* przy rozpoznanym repozytorium mediana pelnej petli spada wobec zakresu „wszystkie".
  *Dane:* 10 pytan (5 par: to samo pytanie z zawezeniem i bez), ta sama maszyna, model bez zmian.
  *Jedna statystyka:* mediana czasu pelnej petli. *Liczba porownan:* 1.
  *Warunek NEGATYWU:* mediana nie spada albo rosnie -> zawezenie zostaje (mniejsza szansa na
  odpowiedz z cudzego repo), ale **nie wolno** go opisywac jako przyspieszenia.
  *Czego wynik NIE uprawnia:* zdania „zadanie 2.7 zrobione" — to osobny pomiar na innym zakresie.
- [ ] 5.3 Przebieg 5.1 na fixturze i zapis liczb (trafienia, falszywe trafienia, rozbicie wg `zrodlo`)
- [ ] 5.4 Przebieg 5.2 na tej maszynie i zapis liczb obok pomiarow z `notes/HANDOFF_most_pytan.md`
- [ ] 5.5 **Slabe aliasy zmierzone 2026-09-16, poprawka wymaga drugiego pomiaru.** Przebieg 5.3 pokazal
  dwa aliasy, ktore lapia zwykle polskie zdania: `projekt car` trafia w „ktory **projekt** ma najwiecej
  otwartych zadan" (jedyne falszywe trafienie), a `kazdy projekt` z listy `wszystkie` trafia w „**czy
  projekt** integracji projektow ma cos pilnego". Usuniecie ich po zobaczeniu wynikow jest **strojeniem
  do fixture** (ZASADY 5.4) — dlatego: (1) najpierw dopisac >= 10 nowych wypowiedzi, ktore tego nie
  dotycza, (2) potem zmienic aliasy, (3) potem przemierzyc, i zapisac obie liczby obok siebie jako
  **drugie** porownanie, jawnie policzone
- [ ] 5.6 Nagrac >= 10 prawdziwych wypowiedzi przez `/ask` i dopisac transkrypcje do fixture z `zrodlo: log`; powtorzyc 5.1 i porownac z wersja syntetyczna

## 6. Domkniecie

- [x] 6.1 Notatka sesji z liczbami i `notes/start.md` (regula 1.1)
- [x] 6.2 `python notes/gen_openspec_status.py`
- [ ] 6.3 `notes/HANDOFF_most_pytan.md`: akapit o warstwie intencji i o tym, jak dodac projekt (jeden wpis w `poc/aliases.json`)
