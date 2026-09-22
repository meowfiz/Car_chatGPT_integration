# OpenSpec task status (generated)

Generated 2026-09-22 18:35. Regenerate with `python notes/gen_openspec_status.py` after updating any change's `tasks.md`. Do not hand-edit this file.

**Overall: 34/108 tasks complete across 4 changes.**

## Summary (most recently updated first)

| Change | Status | Last updated |
|---|---|---|
| [voice-grok-front](changes/voice-grok-front/tasks.md) | 0/24 | 2026-09-22 |
| [poc-carplay-command](changes/poc-carplay-command/tasks.md) | 7/39 | 2026-09-22 |
| [ask-core-client](changes/ask-core-client/tasks.md) | 1/16 | 2026-09-16 |
| [voice-intent](changes/voice-intent/tasks.md) | 26/29 | 2026-09-16 |


---

## voice-grok-front

`0/24` tasks complete.

### 1. Warunki wstepne i porzadki (zanim powstanie kod)

| Done | Task |
|---|---|
| [ ] | 1.1 Potwierdzic plan Grok-a z „Bring Your Own MCP" i zapisac, ktory to plan i co kosztuje; bez tego cala grupa 3 jest bezprzedmiotowa i zostaje sciezka zapasowa |
| [ ] | 1.2 Przeczytac `osaighi/talk-to-claude-code` w calosci i spisac w `notes/research/`, co bierzemy (wzorzec `ask`/`get_reply`, endpointy `/voice/*`, Funnel), a czego nie (ich most do sesji — my mamy orchestrator); **nie kopiowac kodu bez przeczytania licencji** |
| [ ] | 1.3 Zmierzyc, czy orchestrator na pececie odpowiada na `POST /api/agent/chat` z tej maszyny i ile to trwa (3 proby, mediana) — to jest baza czasowa, wobec ktorej liczymy koszt frontu |
| [ ] | 1.4 Zaktualizowac naglowek `monitor/live_sessions.py`: wniosek „nie da sie wejsc do zywego okna" jest prawdziwy **dla CLI**, ale Remote Control (`/remote-control`, Pro/Max/Team/Enterprise) podlacza zywa sesje do claude.ai/code i aplikacji mobilnej — **recznie, bez API i bez CarPlay**. Zapisac obie polowy, zeby nikt nie szukal drugi raz |
| [ ] | 1.5 Zapisac w `notes/HANDOFF_most_pytan.md` podzial rol: Remote Control = telefon w reku, ten front = auto; to nie sa konkurenci |

### 2. Serwer MCP jako cienka warstwa

| Done | Task |
|---|---|
| [ ] | 2.1 `poc/grok_mcp.py`: narzedzia `ask(session, text)` i `get_reply(session)`; `ask` wraca natychmiast ze statusem `working`, `get_reply` oddaje `working` albo `done` z tekstem |
| [ ] | 2.2 Opis narzedzia `get_reply` **wprost** instruuje klienta do ponownego wywolania przy statusie `working` (to jedyne miejsce, gdzie zachowanie klienta zalezy od naszego tekstu) |
| [ ] | 2.3 Kazde zapytanie idzie do `POST /api/agent/chat` orchestratora; **zero wlasnego promptu, zero `claude`, zero wlasnej listy repo** |
| [ ] | 2.4 Test nazywajacy porazke: plik `grok_mcp.py` nie zawiera wywolania `claude` ani sciezek repozytoriow — mutacja (dopisac `subprocess.run(["claude", ...])`) ma go wywalic |
| [ ] | 2.5 Historia rozmowy: n ostatnich par na sesje, wygasanie, izolacja miedzy sesjami; test: dwie sesje nie widza swoich tur |
| [ ] | 2.6 Narzedzie `sessions` (tylko odczyt) na danych z `monitor/live_sessions.py`: repozytorium + zajete/bezczynne; test: prosba o zmiane w zajetym oknie konczy sie odmowa, nie forkiem |
| [ ] | 2.7 Endpointy zapasowe `/voice/ask` i `/voice/reply` z tokenem w sciezce i w query (Skroty iOS nie ustawiaja naglowkow); ten sam przebieg co przez MCP |

### 3. Wystawienie publiczne — dopiero po bramkach

| Done | Task |
|---|---|
| [ ] | 3.1 Limit tempa i log kazdego wywolania (wzorzec z `poc/ask_server.py`), zanim cokolwiek wyjdzie poza tailnet |
| [ ] | 3.2 Zapis **domyslnie wylaczony**; wlaczony idzie wylacznie przez `execute_worker` z jego bramkami i z potwierdzeniem glosem — bramki SHALL NOT byc omijane; test odmowy przy wylaczonym zapisie |
| [ ] | 3.3 Tailscale Funnel ze stabilna nazwa hosta; zapisac nazwe i sposob odtworzenia w HANDOFF |
| [ ] | 3.4 Test bezpieczenstwa: zly token -> 403 i wpis w logu; brak tokenu -> 403; token w query dziala tak samo jak w sciezce |
| [ ] | 3.5 Zapisac wprost w HANDOFF, ze od tego momentu endpoint jest **publiczny**, oraz co z repozytoriow wychodzi do xAI (prywatnosc jako decyzja, nie odkrycie) |

### 4. Prerejestracja i pomiar rozmowy

| Done | Task |
|---|---|
| [ ] | 4.1 PREREJESTRACJA (przed pierwszym przebiegiem, ZASADY 3.3): **hipoteza** — rozmowa wieloturowa utrzymuje kontekst przez >= 4 tury w >= 8/10 przebiegow, a czas do pierwszego slowa odpowiedzi ma mediane <= 20 s; **dane** — 10 rozmow po 5 tur, scenariusze spisane z gory, na postoju; **etykieta** — tura udana = odpowiedz zgodna z danymi monitora i odnoszaca sie do wlasciwej tury wczesniejszej; **jedna statystyka** — odsetek rozmow z zachowanym kontekstem do 4. tury; **liczba testowanych porownan: 2** (liczba tur w historii: 3 wobec 5); **poprawka na wielokrotnosc** — przy dwoch porownaniach raportujemy obie liczby, nie wybieramy lepszej po fakcie; **konfuzje** — dlugosc odpowiedzi orchestratora i to, czy klient rzeczywiscie odpytywal w petli (z logu); **warunek NEGATYWU** — jesli klient przestaje odpytywac przed koncem w > 2/10 przebiegow, front jest nieuzywalny i wracamy do sciezki zapasowej; **czego wynik NIE uprawnia** — nie mowi nic o jezdzie, o hasach w tle ani o zleceniach zapisujacych |
| [ ] | 4.2 Przebieg wg 4.1 na postoju; tabela do `notes/HANDOFF_most_pytan.md` |
| [ ] | 4.3 Liczba tur w historii wybrana **pomiarem** (3 wobec 5), nie zalozeniem; zapisac koszt czasowy kazdej dolozonej tury |
| [ ] | 4.4 Jazda: >= 10 tur, >= 3 rozne tematy, >= 3 tury przy predkosci >= 70 km/h; kazda nieudana tura przypisana do warstwy (klient / siec / orchestrator / model / odtwarzanie) |
| [ ] | 4.5 Wynik negatywny zapisac jako negatywny z przyczyna (ZASADY 5.8) — takze wtedy, gdy przyczyna lezy po stronie Grok-a |

### 5. Decyzja

| Done | Task |
|---|---|
| [ ] | 5.1 Wpis „Decyzja" w HANDOFF z liczbami: czy rozmowa w aucie dziala, na czym stoi, co kosztuje (subskrypcja, publiczny endpoint, prywatnosc), i czy `poc/ask_server.py` mozna wygasic |
| [ ] | 5.2 Aktualizacja `notes/start.md`, notatka sesji, `python notes/gen_openspec_status.py` |

## poc-carplay-command

`7/39` tasks complete.

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
| [x] | 3.7 Wariant C („Monitor GPT", jedyna droga do głosu ChatGPT): most oddaje fakty zamiast zdania pod `?style=facts`, a zdanie układa akcja **Ask ChatGPT** w Skrócie; kroki skrótu w `notes/HANDOFF_most_pytan.md`, uzasadnienie i weryfikacja źródeł w `notes/research/2026-09-22-chatgpt-voice-weryfikacja.md` |
| [ ] | 3.8 PREREJESTRACJA wariantu C (przed pomiarem, ZASADY 3.3): **hipoteza** — wariant C jest zrozumiały nie gorzej niż wersja 1 i kosztuje nie więcej niż 4 s mediany; **dane** — te same 3 pytania co w 5.1, po 5 prób wersji 1 i 5 prób wariantu C, ta sama maszyna, ten sam model mostu, na postoju; **etykieta** — próba udana = odpowiedź zgodna z danymi monitora i słyszalna po polsku; **jedna statystyka** — mediana czasu od końca dyktowania do pierwszego słowa odpowiedzi; **liczba testowanych porównań: 1** (C wobec wersji 1), świadomie osobno od trzech porównań z 5.1, żeby nie rozdmuchiwać wielokrotności; **poprawka** — niepotrzebna przy jednym porównaniu, ale wynik nie może być raportowany łącznie z 5.1 jako „cztery warianty"; **konfuzje** — długość odpowiedzi mostu (facts bywa dłuższe) i model wybrany w akcji ChatGPT, oba zapisywane przy każdej próbie; **warunek NEGATYWU** — mediana dłuższa o > 4 s bez poprawy zrozumiałości ⇒ wariant odrzucony i nie strojony dalej; **czego wynik NIE uprawnia** — nie mówi nic o jeździe, o rozmowie wieloturowej ani o tym, że ChatGPT Voice wywołuje cokolwiek sam |
| [ ] | 3.9 Pomiar wariantu C wg 3.8 na postoju; tabela prób do `notes/HANDOFF_most_pytan.md` obok pozostałych wariantów; wynik negatywny zapisać jako negatywny z przyczyną (ZASADY 5.8) |

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

## ask-core-client

`1/16` tasks complete.

### 1. Zależność od rdzenia

| Done | Task |
|---|---|
| [x] | 1.1 Sprawdzić, że `monitor/ask_core.py` jest w tym repo (dostarcza `install_pack.py` z `project_integration`); jeśli nie ma — `python tools/install_pack.py <to repo> --apply` po stronie monitora i `git pull` **Potwierdzone 2026-09-16**: `monitor/ask_core.py` (306 linii) przyszedł paczką z `project_integration`, drzewo czyste i zgodne z `origin/main`, 25 testów zielonych. Sygnatura: `ask(paths, question, system=, model=, timeout=, context=, use_digest=False) -> (answer, error)`, nigdy nie rzuca; `refresh_repo` / `refresh_all` / `for_speech` / `digest` na miejscu. |
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
| [ ] | 3.6 **Digest: liczby z monitora NIE przenosza sie tutaj** (sesja `project-integration-34`, 2026-09-16). Tam `use_digest=True` dalo mediane 18,4 -> 12,3 s (-33,2%, 9/10 par szybszych), ale **inny prompt (kierowca, trzy zdania), inny model (sonnet) i inny zestaw repo** — ich prerejestracja wprost odmawia wniosku o tej sciezce. Dwie rzeczy wazniejsze od mediany dla nas: (1) **ogon prawie sie nie ruszyl** (p90 26,1 -> 22,9 s, -12%), a to wlasnie ogon decyduje o progu 15 s pelnej petli — digest przesuwa srodek rozkladu, nie najgorszy przypadek; (2) jedna para **zwolnila dwukrotnie** (18,8 -> 35,0 s) przy dluzszej odpowiedzi, u nich otwarte zadanie 3.8. Wniosek: digest wlaczamy **tylko z wlasnym pomiarem** (przebieg naprzemienny w parach, jak w naszym voice-intent 5.2), i deklarujemy **p90, nie mediane**, bo to p90 decyduje o naszym progu. |
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

## voice-intent

`26/29` tasks complete.

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
| [x] | 5.1 **PREREJESTRACJA — trafnosc rozpoznania repozytorium.** *Hipoteza:* reguly + aliasy rozpoznaja wlasciwe repozytorium w **>= 80%** wypowiedzi, w ktorych projekt jest nazwany, przy odsetku falszywych trafien **<= 10%**. *Dane:* fixture `wypowiedzi.json`, **>= 40 wypowiedzi**, w tym >= 5 na kazde repo z mapy maszyny i >= 8 bez nazwanego projektu; kazda wypowiedz ma pole `zrodlo`. *Wykluczenia:* wypowiedzi, w ktorych czlowiek sam nie potrafi wskazac projektu, sa oznaczone `oczekiwane: "*"`, a nie usuwane. *Definicja etykiety:* trafienie = `repo` rowne `oczekiwane`; falszywe trafienie = `repo` to konkretne repo, a `oczekiwane` bylo inne albo `*`; uczciwe `*` nie jest trafieniem ani falszem. *Jedna statystyka:* odsetek trafien; druga (falszywe trafienia) jest **warunkiem bezpieczenstwa**, nie druga hipoteza. *Liczba testowanych porownan:* **1** (jeden prog `min_ratio` = 0,82 zadeklarowany z gory). Strojenie progu po zobaczeniu wynikow = dopasowanie do fixture i musi zostac zapisane jako takie. *Konfuzje do zmierzenia:* udzial wypowiedzi `zrodlo: log` w zbiorze (fixture napisany przy biurku jest latwiejszy niz mowa w aucie) i dlugosc aliasu (aliasy jednoslowne falszuja latwiej). *Warunek NEGATYWU:* trafnosc < 70% albo falszywe trafienia > 10% -> `repo` zostaje na stale `*`, konczymy i nie szukamy trzeciej heurystyki. *Czego wynik NIE uprawnia:* niczego o mowie w jadacym aucie — fixture to tekst, nie nagrania; liczba z prawdziwych nagran moze byc tylko gorsza. |
| [x] | 5.2 **PREREJESTRACJA — czy zawezenie zakresu skraca odpowiedz.** *Hipoteza:* przy rozpoznanym repozytorium mediana pelnej petli spada wobec zakresu „wszystkie". *Dane:* 10 pytan (5 par: to samo pytanie z zawezeniem i bez), ta sama maszyna, model bez zmian. *Jedna statystyka:* mediana czasu pelnej petli. *Liczba porownan:* 1. *Warunek NEGATYWU:* mediana nie spada albo rosnie -> zawezenie zostaje (mniejsza szansa na odpowiedz z cudzego repo), ale **nie wolno** go opisywac jako przyspieszenia. *Czego wynik NIE uprawnia:* zdania „zadanie 2.7 zrobione" — to osobny pomiar na innym zakresie. |
| [x] | 5.3 Przebieg 5.1 na fixturze i zapis liczb (trafienia, falszywe trafienia, rozbicie wg `zrodlo`) |
| [x] | 5.4 Przebieg 5.2 na tej maszynie i zapis liczb obok pomiarow z `notes/HANDOFF_most_pytan.md` **Wynik NEGATYWNY zgodnie z zadeklarowanym warunkiem**: mediana 14,0 s (zawezony) wobec 14,2 s (wszystkie), n=5+5 — roznica tonie w rozrzucie 11,8–25,2 s. Zawezenie zostaje jako ochrona przed odpowiedzia z cudzego drzewa i **nie jest** opisywane jako przyspieszenie. |
| [ ] | 5.5 **Slabe aliasy zmierzone 2026-09-16, poprawka wymaga drugiego pomiaru.** Przebieg 5.3 pokazal dwa aliasy, ktore lapia zwykle polskie zdania: `projekt car` trafia w „ktory **projekt** ma najwiecej otwartych zadan" (jedyne falszywe trafienie), a `kazdy projekt` z listy `wszystkie` trafia w „**czy projekt** integracji projektow ma cos pilnego". Usuniecie ich po zobaczeniu wynikow jest **strojeniem do fixture** (ZASADY 5.4) — dlatego: (1) najpierw dopisac >= 10 nowych wypowiedzi, ktore tego nie dotycza, (2) potem zmienic aliasy, (3) potem przemierzyc, i zapisac obie liczby obok siebie jako **drugie** porownanie, jawnie policzone |
| [ ] | 5.6 Nagrac >= 10 prawdziwych wypowiedzi przez `/ask` i dopisac transkrypcje do fixture z `zrodlo: log`; powtorzyc 5.1 i porownac z wersja syntetyczna |

### 6. Domkniecie

| Done | Task |
|---|---|
| [x] | 6.1 Notatka sesji z liczbami i `notes/start.md` (regula 1.1) |
| [x] | 6.2 `python notes/gen_openspec_status.py` |
| [ ] | 6.3 `notes/HANDOFF_most_pytan.md`: akapit o warstwie intencji i o tym, jak dodac projekt (jeden wpis w `poc/aliases.json`) |
