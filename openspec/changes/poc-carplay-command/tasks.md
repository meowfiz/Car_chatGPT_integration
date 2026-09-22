## 1. Warunki wstępne

- [x] 1.1 Spisać środowisko w `notes/HANDOFF_poc_carplay.md`: model iPhone'a, wersja iOS, wersja HA Companion, wersja HA Core, plan ChatGPT, Apple Intelligence, język Siri, dyktowanie polskie
- [x] 1.2 Sprawdzić, czy iPhone ma aktywny Tailscale w aucie na LTE; jeśli tak, endpoint pytań nie musi być publiczny — zapisać werdykt i czas odpowiedzi `/health` w ms
- [ ] 1.3 Wybrać maszynę w tailnecie na transkrypcję i `claude -p`; potwierdzić, że nie usypia, i zapisać jej nazwę oraz adres
- [ ] 1.4 Włączyć Siri z językiem angielskim i „Hey Siri" przy zablokowanym ekranie; potwierdzić, że w CarPlay reaguje
- [ ] 1.5 Sprawdzić wersję aplikacji HA Companion (wariant B wymaga 26.4+)
- [ ] 1.6 Pecet w pracy: uruchomić `poc/deploy/00_check.ps1` i zamknąć każde `TODO` (python, node, `claude` zalogowany, `faster-whisper` z `ctranslate2==4.5.0`, Tailscale, sklonowane repozytoria z `repos.txt`); zapisać wyjście skryptu w HANDOFF
- [ ] 1.7 Zasilanie peceta w pracy: `poc/deploy/01_power.ps1` (monitory 5 min, sen / hibernacja / dysk nigdy, **unattended sleep 0**, hibernacja wyłączona); po 10 minutach ciemnego ekranu sprawdzić `powercfg /requests` i zapisać, że maszyna nie zasnęła
- [ ] 1.8 Zadania `AskBridge\bridge|watchdog|gitpull` przez `poc/deploy/02_install_tasks.ps1` (z hasłem konta); test twardy: **restart peceta i odpowiedź z tailnetu bez logowania się na niego**
- [ ] 1.9 Zmierzyć `poc/deploy/check_bridge.ps1` na pececie w pracy (czas `/health` w ms, pełna pętla w ms, 3 próby) i wpisać liczby do `notes/HANDOFF_most_pytan.md` obok pomiarów z `desktop-ffshioa`

## 2. Backend pytań w project_monitorze

- [x] 2.1 Most pytań jako jeden plik `poc/ask_server.py` w tym repo (nie w project_monitorze — monitor stoi na RPi, a Claude i repozytoria są na pececie): przyjmuje audio albo tekst, sekret w ścieżce, limit tempa, log każdego wywołania, bind tylko na adres Tailscale
- [x] 2.2 Transkrypcja: faster-whisper lokalnie na maszynie z 1.3, język polski wymuszony; wariant zapasowy przez API transkrypcji, wybierany flagą konfiguracji
- [x] 2.3 Mózg: `claude -p` uruchamiany z dostępem **tylko do odczytu** repozytoriów, bez uprawnień do zapisu i `git push`; kontekst budowany z `/api/state`, zadań i zdarzeń monitora oraz plików `notes/`
- [ ] 2.4 Odpowiedź: zwięzły tekst po polsku, przycięty do długości sensownej do przeczytania głosem; przy długim zadaniu odpowiedź natychmiastowa „przyjąłem" plus powiadomienie HA z wynikiem
- [x] 2.5 Test z komputera: `curl` z plikiem audio po polsku i z samym tekstem; potwierdzić poprawną transkrypcję, sensowną odpowiedź i wpis w logu
- [ ] 2.6 Test odmowy: pytanie proszące o commit lub push ma zostać odrzucone i zapisane w logu
- [ ] 2.7 Skrócić czas odpowiedzi: budować kontekst po stronie mostu (STATUS.md, nagłówki start.md, ostatnie commity) i wkładać go do promptu, żeby model nie szukał w plikach; zmierzyć wobec dzisiejszych 13–34 s

## 3. Skrót iOS (na postoju)

- [ ] 3.1 Zbudować skrót „Monitor": `Record Audio` o stałej długości → POST do `/api/ask` → `Speak Text` polskim głosem; wyłączyć pytanie o zgodę
- [ ] 3.2 Zmierzyć dwie długości nagrania (6 s i 10 s) po 3 próby; wybrać po wynikach, nie po wrażeniu
- [ ] 3.3 Test „Hey Siri, Monitor" na telefonie bez CarPlay: 3 próby; potwierdzić, że nagranie startuje i kończy się samo, bez dotykania ekranu
- [ ] 3.4 Test na postoju z CarPlay: 3 próby; potwierdzić, że sygnał startu i odpowiedź idą przez głośniki auta
- [ ] 3.5 Wariant zapasowy A: drugi skrót z `Dictate Text` i locale `pl_PL` zamiast nagrania; sprawdzić `Show Result`, czy tekst ma polskie znaki; 3 próby na postoju
- [ ] 3.6 Wariant zapasowy B: w HA Companion → CarPlay → Quick Access dodać Assist; 3 próby na postoju, świadomie na frazach zadeklarowanych w `voice_data.yaml`
- [x] 3.7 Wariant C („Monitor GPT", jedyna droga do głosu ChatGPT): most oddaje fakty zamiast zdania pod `?style=facts`, a zdanie układa akcja **Ask ChatGPT** w Skrócie; kroki skrótu w `notes/HANDOFF_most_pytan.md`, uzasadnienie i weryfikacja źródeł w `notes/research/2026-09-22-chatgpt-voice-weryfikacja.md`
- [ ] 3.8 PREREJESTRACJA wariantu C (przed pomiarem, ZASADY 3.3): **hipoteza** — wariant C jest zrozumiały nie gorzej niż wersja 1 i kosztuje nie więcej niż 4 s mediany; **dane** — te same 3 pytania co w 5.1, po 5 prób wersji 1 i 5 prób wariantu C, ta sama maszyna, ten sam model mostu, na postoju; **etykieta** — próba udana = odpowiedź zgodna z danymi monitora i słyszalna po polsku; **jedna statystyka** — mediana czasu od końca dyktowania do pierwszego słowa odpowiedzi; **liczba testowanych porównań: 1** (C wobec wersji 1), świadomie osobno od trzech porównań z 5.1, żeby nie rozdmuchiwać wielokrotności; **poprawka** — niepotrzebna przy jednym porównaniu, ale wynik nie może być raportowany łącznie z 5.1 jako „cztery warianty"; **konfuzje** — długość odpowiedzi mostu (facts bywa dłuższe) i model wybrany w akcji ChatGPT, oba zapisywane przy każdej próbie; **warunek NEGATYWU** — mediana dłuższa o > 4 s bez poprawy zrozumiałości ⇒ wariant odrzucony i nie strojony dalej; **czego wynik NIE uprawnia** — nie mówi nic o jeździe, o rozmowie wieloturowej ani o tym, że ChatGPT Voice wywołuje cokolwiek sam
- [ ] 3.9 Pomiar wariantu C wg 3.8 na postoju; tabela prób do `notes/HANDOFF_most_pytan.md` obok pozostałych wariantów; wynik negatywny zapisać jako negatywny z przyczyną (ZASADY 5.8)

## 4. Scena testowa w Home Assistancie (twardy ślad pętli)

- [ ] 4.1 W repo `HA` dodać scenę `scene.poc_carplay_test` z widocznym efektem; frazy dopisać w `voice/voice_data.yaml` i wygenerować przez `voice/gen_voice_sentences.py`, nie ręcznie w dwóch plikach
- [ ] 4.2 Wyeksponować scenę do Assist przez WebSocket `homeassistant/expose_entity`; potwierdzić z panelu
- [ ] 4.3 Umożliwić wykonanie polecenia z `/api/ask`: rozpoznane polecenie do HA idzie do lokalnego Assist, a nie do modelu; 3 próby z komputera
- [ ] 4.4 Potwierdzić, że potok głosowy HA pozostał w pełni lokalny i nie dodano agenta chmurowego

## 5. Prerejestracja i pomiar w jeździe

- [ ] 5.1 PREREJESTRACJA (przed jazdą): hipoteza „ścieżka główna daje ≥ 7/10 udanych prób, medianę czasu odpowiedzi ≤ 15 s i ≥ 8/10 poprawnych transkrypcji”; pytania: „co się dzieje z projektem Car ChatGPT”, „ile zadań zostało w projekcie X”, „kiedy była ostatnia sesja w repozytorium HA”, plus polecenie „włącz scenę testową”; definicja udanej próby = odpowiedź zgodna z danymi monitora i słyszalna po polsku; statystyki: udane/wszystkie, transkrypcje poprawne/wszystkie, mediana i max czasu; liczba testowanych porównań: 3 (ścieżka główna, wariant A, wariant B); warunek negatywu jak w spec; wynik nie uprawnia do wniosków o rozmowie wieloturowej ani o operacjach zapisujących
- [ ] 5.2 Protokół rejestracji: nagranie audio z timestampem plus log endpointu i logbook HA; tabela prób w HANDOFF z kolumnami: nr, pytanie, wariant, wynik, transkrypcja OK?, trafność, t_odpowiedz [s], prędkość, uwagi
- [ ] 5.3 Jazda pomiarowa: ≥ 10 prób ścieżki głównej, ≥ 3 różne pytania, ≥ 3 próby przy prędkości ≥ 70 km/h
- [ ] 5.4 Ta sama jazda: ≥ 5 prób wariantu A; jeśli wersja aplikacji pozwala, ≥ 5 prób wariantu B
- [ ] 5.5 Opracowanie: policzyć statystyki z nagrania i logów, wpisać do HANDOFF; każdą nieudaną próbę przypisać do warstwy (Siri / nagranie / transkrypcja / sieć / model / odtwarzanie)
- [ ] 5.6 Porównać transkrypcję Whispera z `Dictate Text` na tych samych nagraniach z hałasu — to rozstrzyga, czy warstwa Apple wystarcza

## 6. Eksperyment E1 (tani test, niezależny od reszty)

- [ ] 6.1 Wystawić publiczny adres z logiem user-agenta, IP i czasu; poprosić ChatGPT o jego otwarcie w tekście, głosem i głosem w CarPlay, po 3 próby
- [ ] 6.2 Werdykt: czy w logu pojawia się `ChatGPT-User` z IP z listy OpenAI, czy treść wraca wiernie czy streszczona, jakie opóźnienie, czy powtórka nie idzie z cache; zapis do HANDOFF jako osobna tabela

## 7. Decyzja i zamknięcie

- [ ] 7.1 Wpis „Decyzja" w HANDOFF: PoC zaliczony / negatywny, z liczbami; osobne zdania o transkrypcji polskiej, o czasie odpowiedzi i o wyniku E1; rekomendacja, czy budować Command Center i na jakim wejściu
- [ ] 7.2 Aktualizacja `notes/start.md`, notatka sesji, `python notes/gen_openspec_status.py`
