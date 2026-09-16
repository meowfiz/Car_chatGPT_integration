# OpenSpec task status (generated)

Generated 2026-09-16 17:05. Regenerate with `python notes/gen_openspec_status.py` after updating any change's `tasks.md`. Do not hand-edit this file.

**Overall: 28/80 tasks complete across 3 changes.**

## Summary (most recently updated first)

| Change | Status | Last updated |
|---|---|---|
| [voice-intent](changes/voice-intent/tasks.md) | 22/29 | 2026-09-16 |
| [ask-core-client](changes/ask-core-client/tasks.md) | 0/15 | 2026-09-16 |
| [poc-carplay-command](changes/poc-carplay-command/tasks.md) | 6/36 | 2026-09-15 |


---

## voice-intent

`22/29` tasks complete.

### 1. Schemat i dane

| Done | Task |
|---|---|
| [x] | 1.1 Schemat intencji v1 opisany w `design.md` i w specyfikacji (`intent`, `repo`, `text`, `limit_zdan`, `v`); uzasadnienie kazdego pola, w tym dlaczego `text` zostaje cala wypowiedzia |
| [x] | 1.2 `poc/aliases.json`: tablica aliasow jako **dane** (klucz = nazwa kanoniczna repo, wartosc = mowione warianty), z `min_ratio` i wersja pliku; dodanie projektu nie wymaga zmiany kodu |
| [x] | 1.3 Nazwy kanoniczne czytane z `~/.claude/monitor_repos.env` (jedno zrodlo prawdy); alias wskazujacy na nieznane repo wypisywany przy starcie jako ostrzezenie, nie ignorowany po cichu |

### 2. Parser deterministyczny

| Done | Task |
|---|---|
| [x] | 2.1 `poc/intent.py`: `normalize()` (male litery, polskie znaki na ASCII, tylko `[a-z0-9 ]`) — wspolna podstawa wszystkich porownan |
| [x] | 2.2 `match_repo()`: dopasowanie aliasu po n-gramach slow o dlugosci aliasu, `difflib.SequenceMatcher`, prog `min_ratio` z pliku danych; zwraca `(repo, powod)` gdzie powod to `exact` / `fuzzy` / `explicit-all` / `ambiguous` / `no-match` (dwa repo blizej niz 0,02 od siebie to nie decyzja, tylko rzut moneta -> `*`) |
| [x] | 2.3 `parse_limit()`: „w jednym/dwoch/trzech/czterech/pieciu zdaniach" oraz cyfry („w 2 zdaniach"); brak liczby = `None`, bez zgadywania z „krotko" |
| [x] | 2.4 `parse()`: slowa kluczowe intencji (`note`, `queue`), domyslnie `ask`; zwraca pelna strukture v1 |
| [x] | 2.5 Zero dodatkowych wywolan modelu — decyzja i jej uzasadnienie w `design.md` („Rezerwa modelowa") |

### 3. Wpiecie w most

| Done | Task |
|---|---|
| [x] | 3.1 `ask_server.py` wola `intent.parse()` po transkrypcji, przed `ask_claude` |
| [x] | 3.2 `intent: note \| queue` -> HTTP 200 z jednym zdaniem odmowy po polsku (skrot czyta tresc, nie kod bledu); wpis w logu |
| [x] | 3.3 Rozpoznane `repo` zaweza zakres: `claude -p` startuje w tym katalogu i nie dostaje `--add-dir` do pozostalych |
| [x] | 3.4 Instrukcja zakresu w prompcie: odpowiedz zaczyna sie od nazwy repozytorium (zamiast pytania potwierdzajacego); limit zdan doklejany, gdy podany |
| [x] | 3.5 Log zapisuje `intent`, `repo` i **powod** dopasowania (`explicit-all` vs `no-match` to dwie rozne rzeczy, inaczej nie da sie policzyc trafnosci) |
| [x] | 3.6 Odpowiedz `?format=json` niesie strukture intencji, zeby dalo sie mierzyc bez czytania logu |

### 4. Testy nazywajace porazke (ZASADY 4.4)

| Done | Task |
|---|---|
| [x] | 4.1 Fixture wypowiedzi `project_files/python/tests/fixtures/wypowiedzi.json` z jawnym polem `zrodlo`: `log` (prawdziwa transkrypcja Whispera) albo `syntetyczna` (napisana recznie) |
| [x] | 4.2 Test: prawdziwa transkrypcja „Carcha gpt integration" trafia w `Car_chatGPT_integration` — porazka, ktorej zapobiega: parser dzialajacy tylko na poprawnie wymowionych nazwach |
| [x] | 4.3 Test: „zanotuj..." nie jest pytaniem, a odmowa nie ma kodu bledu — porazka: cicha zamiana zapisu w pytanie |
| [x] | 4.4 Test: brak dopasowania daje `*` z powodem `no-match`, a „wszystkie projekty" daje `*` z powodem `explicit-all` — porazka: pomiar trafnosci liczacy nierozpoznanie jako sukces |
| [x] | 4.5 Test: alias spoza mapy repozytoriow jest raportowany, a parser dziala dalej |
| [x] | 4.6 Sprawdzenie mutacja kazdego z powyzszych (wprowadz blad z powrotem, test ma paść) i zapis wyniku w notatce sesji |

### 5. Pomiar (PREREJESTRACJA przed przebiegiem, ZASADY 3.3)

| Done | Task |
|---|---|
| [ ] | 5.1 **PREREJESTRACJA — trafnosc rozpoznania repozytorium.** *Hipoteza:* reguly + aliasy rozpoznaja wlasciwe repozytorium w **>= 80%** wypowiedzi, w ktorych projekt jest nazwany, przy odsetku falszywych trafien **<= 10%**. *Dane:* fixture `wypowiedzi.json`, **>= 40 wypowiedzi**, w tym >= 5 na kazde repo z mapy maszyny i >= 8 bez nazwanego projektu; kazda wypowiedz ma pole `zrodlo`. *Wykluczenia:* wypowiedzi, w ktorych czlowiek sam nie potrafi wskazac projektu, sa oznaczone `oczekiwane: "*"`, a nie usuwane. *Definicja etykiety:* trafienie = `repo` rowne `oczekiwane`; falszywe trafienie = `repo` to konkretne repo, a `oczekiwane` bylo inne albo `*`; uczciwe `*` nie jest trafieniem ani falszem. *Jedna statystyka:* odsetek trafien; druga (falszywe trafienia) jest **warunkiem bezpieczenstwa**, nie druga hipoteza. *Liczba testowanych porownan:* **1** (jeden prog `min_ratio` = 0,82 zadeklarowany z gory). Strojenie progu po zobaczeniu wynikow = dopasowanie do fixture i musi zostac zapisane jako takie. *Konfuzje do zmierzenia:* udzial wypowiedzi `zrodlo: log` w zbiorze (fixture napisany przy biurku jest latwiejszy niz mowa w aucie) i dlugosc aliasu (aliasy jednoslowne falszuja latwiej). *Warunek NEGATYWU:* trafnosc < 70% albo falszywe trafienia > 10% -> `repo` zostaje na stale `*`, konczymy i nie szukamy trzeciej heurystyki. *Czego wynik NIE uprawnia:* niczego o mowie w jadacym aucie — fixture to tekst, nie nagrania; liczba z prawdziwych nagran moze byc tylko gorsza. |
| [ ] | 5.2 **PREREJESTRACJA — czy zawezenie zakresu skraca odpowiedz.** *Hipoteza:* przy rozpoznanym repozytorium mediana pelnej petli spada wobec zakresu „wszystkie". *Dane:* 10 pytan (5 par: to samo pytanie z zawezeniem i bez), ta sama maszyna, model bez zmian. *Jedna statystyka:* mediana czasu pelnej petli. *Liczba porownan:* 1. *Warunek NEGATYWU:* mediana nie spada albo rosnie -> zawezenie zostaje (mniejsza szansa na odpowiedz z cudzego repo), ale **nie wolno** go opisywac jako przyspieszenia. *Czego wynik NIE uprawnia:* zdania „zadanie 2.7 zrobione" — to osobny pomiar na innym zakresie. |
| [ ] | 5.3 Przebieg 5.1 na fixturze i zapis liczb (trafienia, falszywe trafienia, rozbicie wg `zrodlo`) |
| [ ] | 5.4 Przebieg 5.2 na tej maszynie i zapis liczb obok pomiarow z `notes/HANDOFF_most_pytan.md` |
| [ ] | 5.5 **Slabe aliasy zmierzone 2026-09-16, poprawka wymaga drugiego pomiaru.** Przebieg 5.3 pokazal dwa aliasy, ktore lapia zwykle polskie zdania: `projekt car` trafia w „ktory **projekt** ma najwiecej otwartych zadan" (jedyne falszywe trafienie), a `kazdy projekt` z listy `wszystkie` trafia w „**czy projekt** integracji projektow ma cos pilnego". Usuniecie ich po zobaczeniu wynikow jest **strojeniem do fixture** (ZASADY 5.4) — dlatego: (1) najpierw dopisac >= 10 nowych wypowiedzi, ktore tego nie dotycza, (2) potem zmienic aliasy, (3) potem przemierzyc, i zapisac obie liczby obok siebie jako **drugie** porownanie, jawnie policzone |
| [ ] | 5.6 Nagrac >= 10 prawdziwych wypowiedzi przez `/ask` i dopisac transkrypcje do fixture z `zrodlo: log`; powtorzyc 5.1 i porownac z wersja syntetyczna |

### 6. Domkniecie

| Done | Task |
|---|---|
| [x] | 6.1 Notatka sesji z liczbami i `notes/start.md` (regula 1.1) |
| [x] | 6.2 `python notes/gen_openspec_status.py` |
| [ ] | 6.3 `notes/HANDOFF_most_pytan.md`: akapit o warstwie intencji i o tym, jak dodac projekt (jeden wpis w `poc/aliases.json`) |

## ask-core-client

`0/15` tasks complete.

### 1. Zależność od rdzenia

| Done | Task |
|---|---|
| [ ] | 1.1 Sprawdzić, że `monitor/ask_core.py` jest w tym repo (dostarcza `install_pack.py` z `project_integration`); jeśli nie ma — `python tools/install_pack.py <to repo> --apply` po stronie monitora i `git pull` |
| [ ] | 1.2 PREREJESTRACJA pomiaru: przed zmianą zmierzyć obecne 10 pytań (mediana i p90 pełnej pętli oraz samego `claude`), zapisać w notatce; warunek negatywu: jeśli po przejściu na rdzeń mediana rośnie o > 15%, wracamy do własnego `ask_claude` i mówimy dlaczego |

### 2. Przeniesienie świeżości do rdzenia (nasz wkład)

| Done | Task |
|---|---|
| [ ] | 2.1 `sync_repo` → `ask_core.refresh_repo(path, timeout)` bez zmiany semantyki: `pull --ff-only` tylko przy czystym drzewie, nigdy rebase, nigdy push; zwraca stan („podciagniete z remote" / „bez zmian na remote" / „lokalne zmiany, nie odswiezam" / „NIE odswiezone") |
| [ ] | 2.2 `sync_all` → `ask_core.refresh_all(paths, timeout)` (równolegle, jak dziś: zmierzone 1,95 s dla czterech repo) |
| [ ] | 2.3 Testy z `project_files/python/tests/test_ask_server.py` dotyczące świeżości przenieść do paczki razem z kodem; tutaj zostaje test, że `ask_server` **woła** rdzeń (a nie że rdzeń działa) |

### 3. `ask_server.py` jako klient

| Done | Task |
|---|---|
| [ ] | 3.1 `ask_claude(question)` → `ask_core.ask(REPOS, question, system=SYSTEM, model=MODEL, timeout=CLAUDE_TIMEOUT)`; `SYSTEM` (kierowca: trzy zdania, bez markdown) zostaje w tym repo jako parametr |
| [ ] | 3.2 `for_speech` → `ask_core.for_speech`; usunąć lokalną kopię po potwierdzeniu, że testy na bloki kodu i znaki markdown przechodzą na wersji z rdzenia |
| [ ] | 3.3 `repo_paths()`: domyślnie `~/.claude/monitor_repos.env`, `ASK_REPOS` / `ASK_ROOT` jako nadpisanie; test: pusta mapa i brak zmiennych → czytelny błąd, nie cisza |
| [ ] | 3.4 Sprawdzić na tej maszynie, że pytanie z limitem („w dwóch zdaniach") rzeczywiście dociera do modelu — rdzeń przekazuje pytanie przez **stdin**, nie w argv (defekt monitora z 2026-09-16); test: żaden element argv nie zawiera `\n` |
| [ ] | 3.5 Powtórzyć pomiar 1.2 i porównać z prerejestracją; liczby w notatce sesji |

### 4. Jeden rezydent na maszynę

| Done | Task |
|---|---|
| [ ] | 4.1 `poc/deploy/02_install_tasks.ps1`: dodatkowe zadanie „przy logowaniu" → `python <repo>\monitor\ask_worker.py --spawn` (idempotentne: worker sam sprawdza blokadę i wychodzi, gdy inny działa) |
| [ ] | 4.2 `poc/deploy/check_bridge.ps1`: pokazać też stan workera (`ask_worker.py --status`) |
| [ ] | 4.3 `poc/deploy/README_PRACA.md`: jeden akapit, że pecet w pracy odpowiada wtedy **obiema** drogami — głosem z auta i na pytania z Home Assistanta |

### 5. Domknięcie

| Done | Task |
|---|---|
| [ ] | 5.1 Notatka sesji z liczbami (przed/po) i wpis w `notes/start.md` |
| [ ] | 5.2 Zaznaczyć w `project_integration/openspec/changes/ask-core/tasks.md` zadania 2.2 i 2.3 jako zrobione po stronie klienta |

## poc-carplay-command

`6/36` tasks complete.

### 1. Warunki wstępne

| Done | Task |
|---|---|
| [x] | 1.1 Spisać środowisko w `notes/HANDOFF_poc_carplay.md`: model iPhone'a, wersja iOS, wersja HA Companion, wersja HA Core, plan ChatGPT, Apple Intelligence, język Siri, dyktowanie polskie |
| [x] | 1.2 Sprawdzić, czy iPhone ma aktywny Tailscale w aucie na LTE; jeśli tak, endpoint pytań nie musi być publiczny — zapisać werdykt i czas odpowiedzi `/health` w ms |
| [ ] | 1.3 Wybrać maszynę w tailnecie na transkrypcję i `claude -p`; potwierdzić, że nie usypia, i zapisać jej nazwę oraz adres |
| [ ] | 1.4 Włączyć Siri z językiem angielskim i „Hey Siri" przy zablokowanym ekranie; potwierdzić, że w CarPlay reaguje |
| [ ] | 1.5 Sprawdzić wersję aplikacji HA Companion (wariant B wymaga 26.4+) |
| [ ] | 1.6 Pecet w pracy: uruchomić `poc/deploy/00_check.ps1` i zamknąć każde `TODO` (python, node, `claude` zalogowany, `faster-whisper` z `ctranslate2==4.5.0`, Tailscale, sklonowane repozytoria z `repos.txt`); zapisać wyjście skryptu w HANDOFF |
| [ ] | 1.7 Zasilanie peceta w pracy: `poc/deploy/01_power.ps1` (monitory 5 min, sen / hibernacja / dysk nigdy, **unattended sleep 0**, hibernacja wyłączona); po 10 minutach ciemnego ekranu sprawdzić `powercfg /requests` i zapisać, że maszyna nie zasnęła |
| [ ] | 1.8 Zadania `AskBridge\bridge\|watchdog\|gitpull` przez `poc/deploy/02_install_tasks.ps1` (z hasłem konta); test twardy: **restart peceta i odpowiedź z tailnetu bez logowania się na niego** |
| [ ] | 1.9 Zmierzyć `poc/deploy/check_bridge.ps1` na pececie w pracy (czas `/health` w ms, pełna pętla w ms, 3 próby) i wpisać liczby do `notes/HANDOFF_most_pytan.md` obok pomiarów z `desktop-ffshioa` |

### 2. Backend pytań w project_monitorze

| Done | Task |
|---|---|
| [x] | 2.1 Most pytań jako jeden plik `poc/ask_server.py` w tym repo (nie w project_monitorze — monitor stoi na RPi, a Claude i repozytoria są na pececie): przyjmuje audio albo tekst, sekret w ścieżce, limit tempa, log każdego wywołania, bind tylko na adres Tailscale |
| [x] | 2.2 Transkrypcja: faster-whisper lokalnie na maszynie z 1.3, język polski wymuszony; wariant zapasowy przez API transkrypcji, wybierany flagą konfiguracji |
| [x] | 2.3 Mózg: `claude -p` uruchamiany z dostępem **tylko do odczytu** repozytoriów, bez uprawnień do zapisu i `git push`; kontekst budowany z `/api/state`, zadań i zdarzeń monitora oraz plików `notes/` |
| [ ] | 2.4 Odpowiedź: zwięzły tekst po polsku, przycięty do długości sensownej do przeczytania głosem; przy długim zadaniu odpowiedź natychmiastowa „przyjąłem" plus powiadomienie HA z wynikiem |
| [x] | 2.5 Test z komputera: `curl` z plikiem audio po polsku i z samym tekstem; potwierdzić poprawną transkrypcję, sensowną odpowiedź i wpis w logu |
| [ ] | 2.6 Test odmowy: pytanie proszące o commit lub push ma zostać odrzucone i zapisane w logu |
| [ ] | 2.7 Skrócić czas odpowiedzi: budować kontekst po stronie mostu (STATUS.md, nagłówki start.md, ostatnie commity) i wkładać go do promptu, żeby model nie szukał w plikach; zmierzyć wobec dzisiejszych 13–34 s |

### 3. Skrót iOS (na postoju)

| Done | Task |
|---|---|
| [ ] | 3.1 Zbudować skrót „Monitor": `Record Audio` o stałej długości → POST do `/api/ask` → `Speak Text` polskim głosem; wyłączyć pytanie o zgodę |
| [ ] | 3.2 Zmierzyć dwie długości nagrania (6 s i 10 s) po 3 próby; wybrać po wynikach, nie po wrażeniu |
| [ ] | 3.3 Test „Hey Siri, Monitor" na telefonie bez CarPlay: 3 próby; potwierdzić, że nagranie startuje i kończy się samo, bez dotykania ekranu |
| [ ] | 3.4 Test na postoju z CarPlay: 3 próby; potwierdzić, że sygnał startu i odpowiedź idą przez głośniki auta |
| [ ] | 3.5 Wariant zapasowy A: drugi skrót z `Dictate Text` i locale `pl_PL` zamiast nagrania; sprawdzić `Show Result`, czy tekst ma polskie znaki; 3 próby na postoju |
| [ ] | 3.6 Wariant zapasowy B: w HA Companion → CarPlay → Quick Access dodać Assist; 3 próby na postoju, świadomie na frazach zadeklarowanych w `voice_data.yaml` |

### 4. Scena testowa w Home Assistancie (twardy ślad pętli)

| Done | Task |
|---|---|
| [ ] | 4.1 W repo `HA` dodać scenę `scene.poc_carplay_test` z widocznym efektem; frazy dopisać w `voice/voice_data.yaml` i wygenerować przez `voice/gen_voice_sentences.py`, nie ręcznie w dwóch plikach |
| [ ] | 4.2 Wyeksponować scenę do Assist przez WebSocket `homeassistant/expose_entity`; potwierdzić z panelu |
| [ ] | 4.3 Umożliwić wykonanie polecenia z `/api/ask`: rozpoznane polecenie do HA idzie do lokalnego Assist, a nie do modelu; 3 próby z komputera |
| [ ] | 4.4 Potwierdzić, że potok głosowy HA pozostał w pełni lokalny i nie dodano agenta chmurowego |

### 5. Prerejestracja i pomiar w jeździe

| Done | Task |
|---|---|
| [ ] | 5.1 PREREJESTRACJA (przed jazdą): hipoteza „ścieżka główna daje ≥ 7/10 udanych prób, medianę czasu odpowiedzi ≤ 15 s i ≥ 8/10 poprawnych transkrypcji”; pytania: „co się dzieje z projektem Car ChatGPT”, „ile zadań zostało w projekcie X”, „kiedy była ostatnia sesja w repozytorium HA”, plus polecenie „włącz scenę testową”; definicja udanej próby = odpowiedź zgodna z danymi monitora i słyszalna po polsku; statystyki: udane/wszystkie, transkrypcje poprawne/wszystkie, mediana i max czasu; liczba testowanych porównań: 3 (ścieżka główna, wariant A, wariant B); warunek negatywu jak w spec; wynik nie uprawnia do wniosków o rozmowie wieloturowej ani o operacjach zapisujących |
| [ ] | 5.2 Protokół rejestracji: nagranie audio z timestampem plus log endpointu i logbook HA; tabela prób w HANDOFF z kolumnami: nr, pytanie, wariant, wynik, transkrypcja OK?, trafność, t_odpowiedz [s], prędkość, uwagi |
| [ ] | 5.3 Jazda pomiarowa: ≥ 10 prób ścieżki głównej, ≥ 3 różne pytania, ≥ 3 próby przy prędkości ≥ 70 km/h |
| [ ] | 5.4 Ta sama jazda: ≥ 5 prób wariantu A; jeśli wersja aplikacji pozwala, ≥ 5 prób wariantu B |
| [ ] | 5.5 Opracowanie: policzyć statystyki z nagrania i logów, wpisać do HANDOFF; każdą nieudaną próbę przypisać do warstwy (Siri / nagranie / transkrypcja / sieć / model / odtwarzanie) |
| [ ] | 5.6 Porównać transkrypcję Whispera z `Dictate Text` na tych samych nagraniach z hałasu — to rozstrzyga, czy warstwa Apple wystarcza |

### 6. Eksperyment E1 (tani test, niezależny od reszty)

| Done | Task |
|---|---|
| [ ] | 6.1 Wystawić publiczny adres z logiem user-agenta, IP i czasu; poprosić ChatGPT o jego otwarcie w tekście, głosem i głosem w CarPlay, po 3 próby |
| [ ] | 6.2 Werdykt: czy w logu pojawia się `ChatGPT-User` z IP z listy OpenAI, czy treść wraca wiernie czy streszczona, jakie opóźnienie, czy powtórka nie idzie z cache; zapis do HANDOFF jako osobna tabela |

### 7. Decyzja i zamknięcie

| Done | Task |
|---|---|
| [ ] | 7.1 Wpis „Decyzja" w HANDOFF: PoC zaliczony / negatywny, z liczbami; osobne zdania o transkrypcji polskiej, o czasie odpowiedzi i o wyniku E1; rekomendacja, czy budować Command Center i na jakim wejściu |
| [ ] | 7.2 Aktualizacja `notes/start.md`, notatka sesji, `python notes/gen_openspec_status.py` |
