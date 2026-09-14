## 1. Warunki wstępne (na komputerze i telefonie, poza autem)

- [ ] 1.1 Spisać środowisko w `notes/HANDOFF_poc_carplay.md`: model iPhone'a, wersja iOS, wersja HA Companion, wersja HA Core, plan ChatGPT, czy iPhone ma Apple Intelligence, **na jaki język ustawiona jest Siri**, czy polska klawiatura z dyktowaniem jest włączona
- [ ] 1.2 W repo `HA` dodać scenę `scene.poc_carplay_test` (widoczny efekt, np. jedno światło + notyfikacja na telefon) z polskim aliasem Assist „scena testowa”; sprawdzić z panelu HA, że logbook zapisuje aktywację
- [ ] 1.3 Sprawdzić z iPhone'a na LTE (Wi-Fi wyłączone) osiągalność HA przez URL Tailscale i przez URL zewnętrzny aplikacji; zapisać, który działa i czas odpowiedzi `/api/` w ms
- [ ] 1.4 Utworzyć pipeline Assist „poc” z **językiem polskim** i agentem wbudowanym HA; w panelu Assist wpisać „włącz scenę testową” i potwierdzić aktywację sceny + polską treść odpowiedzi

## 2. Skrót „Home” i weryfikacja polskiego (na postoju)

- [ ] 2.1 Zbudować skrót o angielskiej nazwie „Home”: `Dictate Text` z wymuszonym locale `pl_PL` → HA `Assist prompt` (pipeline „poc”) → `Speak Text` z jawnie wybranym głosem polskim; ustawić „bez pytania o zgodę” dla akcji HA
- [ ] 2.2 Zweryfikować wymuszenie locale: tymczasowo dodać `Show Result` po dyktowaniu, wypowiedzieć „włącz scenę testową” i potwierdzić polski zapis z polskimi znakami; jeśli locale jest ignorowane, przetestować wariant z polską klawiaturą jako domyślną dyktowania i zapisać, który działa
- [ ] 2.3 Test na telefonie bez CarPlay: „Hey Siri, Home” → polskie polecenie → scena w logbooku; 3 próby (OK/błąd, transkrypcja OK?, czas do akcji z zegara HA)
- [ ] 2.4 Test na postoju z CarPlay podłączonym: 3 próby jak w 2.3; potwierdzić, że dyktowanie startuje i kończy się bez dotykania ekranu, oraz że dyktowanie i polska odpowiedź idą przez głośniki auta, a nie przez telefon
- [ ] 2.5 Zbudować fallback A: skrót „Scene” = `Activate scene` → `Speak Text` stały polski tekst; 3 próby na postoju z CarPlay (pętla bez rozpoznawania mowy)
- [ ] 2.6 Przygotować fallback B: w HA Companion → CarPlay → Quick Access dodać „Assist” z pipeline „poc” (wymaga iOS 26.4+); 3 próby na postoju, ten sam zestaw polskich poleceń

## 3. Prerejestracja i pomiar w jeździe

- [ ] 3.1 PREREJESTRACJA (przed jazdą): hipoteza „ścieżka główna daje ≥ 7/10 udanych prób i medianę czasu do akcji ≤ 10 s, przy ≥ 8/10 poprawnych transkrypcji polskich”; polecenia: „włącz scenę testową”, „wyłącz scenę testową”, „jaki jest stan sceny testowej”; definicja udanej próby = akcja w logbooku HA + polska odpowiedź głosem słyszalna; statystyki: udane/wszystkie, transkrypcje poprawne/wszystkie, mediana i max czasu do akcji, mediana i max czasu do odpowiedzi; liczba testowanych porównań: 3 (ścieżka główna, fallback A, fallback B); warunek negatywu jak w spec; wynik nie uprawnia do wniosków o innych mostach, o rozmowie wieloturowej ani o poleceniach spoza tej trójki
- [ ] 3.2 Protokół rejestracji: nagranie audio z timestampem (dyktafon lub drugi telefon) + eksport logbooka HA dla `scene.poc_carplay_test` za czas jazdy; tabela prób w `notes/HANDOFF_poc_carplay.md` z kolumnami: nr, polecenie, wynik, transkrypcja OK?, t_akcja [s], t_odpowiedz [s], prędkość ~km/h, uwagi (hałas, zasięg)
- [ ] 3.3 Jazda pomiarowa: ≥ 10 prób ścieżki głównej w ruchu, ≥ 3 różne polecenia, ≥ 3 próby przy prędkości ≥ 70 km/h (hałas); zapis każdej próby od razu (głosem na nagraniu)
- [ ] 3.4 Ta sama jazda: ≥ 5 prób fallbacku A; jeśli iOS ≥ 26.4: ≥ 5 prób fallbacku B tymi samymi poleceniami (porównanie dyktowania Apple ze STT Home Assistanta na polskim)
- [ ] 3.5 Opracowanie: policzyć statystyki z 3.1 z nagrania + logbooka (nie z pamięci), wpisać do HANDOFF; każdą nieudaną próbę przypisać do warstwy (Siri nie uruchomiła skrótu / dyktowanie nie wystartowało / transkrypcja polska błędna / Assist nie zrozumiał poprawnej transkrypcji / HA nieosiągalny / brak odpowiedzi głosem)

## 4. ChatGPT jako mózg rozmowy (założenie użytkownika przyjęte jako pewnik)

- [ ] 4.1 Dodać w HA integrację OpenAI Conversation jako agent drugiego pipeline'u „poc-llm” (język polski) ze sterowaniem HA; drugi skrót „Home Plus” wskazujący ten pipeline
- [ ] 4.2 ≥ 5 prób „Home Plus” w tych samych warunkach, osobna tabela (reguła 6.2: nie mieszać z 3.x); porównać czas do akcji i rozumienie swobodnych polskich poleceń z odmianą („zrób jasno w salonie”, „zgaś wszystko na dole”)
- [ ] 4.3 E1 — eksperyment „czy ChatGPT sam pobierze mój link”: wystawić publiczny endpoint pod krótkim, wymawialnym adresem, logujący user-agent, IP i czas; poprosić ChatGPT o otwarcie adresu (a) w tekście na telefonie, (b) głosem, (c) głosem w CarPlay, po 3 próby każdy wariant
- [ ] 4.4 E1 — wynik: czy w logu pojawia się `ChatGPT-User` (zweryfikować IP wobec https://openai.com/chatgpt-user.json), czy model czyta treść strony wiernie czy streszcza, opóźnienie, czy powtórne wywołanie nie idzie z cache; zapis do HANDOFF jako osobna tabela wraz z werdyktem „wersja A żyje / nie żyje”
- [ ] 4.5 E2 — most do Claude'a: minimalny endpoint (dodatek HA lub kontener w tailnecie) przyjmujący **polecenie z zamkniętej listy** plus tekst, uruchamiający `claude -p` i zwracający tekst wyniku; sekret w ścieżce, limit tempa, log każdego wywołania
- [ ] 4.6 E2 — wystawić w HA `script.claude_task` z opisem dla LLM i `rest_command` do endpointu z 4.5; sprawdzić z panelu Assist, że agent OpenAI sam wybiera to narzędzie dla polecenia typu „sprawdź, co się dzieje z projektem X”
- [ ] 4.7 E2 — wariant długiego zadania: endpoint odpowiada natychmiast „przyjąłem, wynik pod <link>”, a po zakończeniu wysyła powiadomienie HA na telefon; zmierzyć czas od polecenia do potwierdzenia głosem i od polecenia do powiadomienia z wynikiem, ≥ 3 próby
- [ ] 4.8 Przegląd bezpieczeństwa mostu przed pierwszym użyciem poza domem: whitelista operacji, brak uprawnień do `git push`, log wszystkich wywołań, sprawdzenie, że treść wracająca z sieci nie trafia do agenta jako instrukcja (pośrednie prompt injection)

## 5. Decyzja i zamknięcie

- [ ] 5.1 Wpis „Decyzja” w `notes/HANDOFF_poc_carplay.md`: PoC zaliczony / negatywny, z liczbami; osobne zdanie o polskim (czy dyktowanie `pl_PL` wystarcza, czy trzeba STT po stronie HA); osobne zdanie o wyniku E1 (czy Command Center ma mieć wejście „URL dla ChatGPT”, czy tylko „narzędzie dla agenta w HA”); rekomendacja: budować Command Center na moście Siri+Skróty, czekać na apps w ChatGPT Voice, albo własna aplikacja CarPlay
- [ ] 5.2 Aktualizacja `notes/start.md` (sekcja „Ostatnia sesja” i „Czym jest ten projekt” o wynik PoC), notatka sesji, `python notes/gen_openspec_status.py`
