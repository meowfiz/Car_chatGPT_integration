## 1. Plan i kontrakt (to okno)

- [x] 1.1 proposal, design (D1-D9), spec `car-dialog` - 2026-10-29
- [x] 1.2 Tabela scenariuszy e2e `notes/car_dialog_scenariusze.md`: wypowiedź -> oczekiwany `outcome`/`state`/początek `text` (>= 30 wierszy, w tym graniczne z R1); to jest wspólny kontrakt dla testów huba i e2e
- [x] 1.3 Zlecenie okna `project_integration` (grupa 2) i okna `HA` (grupa 3) wysłane; wyslane przez send_task.py 2026-10-29 (oba OK, bridge GEIH38C), godzina w notatce sesji

## 2. Hub: `project_integration` (okno huba)

- [x] 2.1 O1: zmierzyć, czy relay drugiej maszyny zwraca odpowiedź okna (`/task` jednokierunkowy?); wynik w `notes/HANDOFF_car_dialog.md`; jeśli brak - dołożyć `GET /reply` -- zrobione: relay jednokierunkowy, odpowiedz z `/spoken` po 4,2-6,1 s, `GET /reply` zbedny (raport huba 594b9c9)
- [x] 2.2 `tools/car_dialog.py`: czyste `decide(state, text, world)`, parser komend (D2), wybór maszyny (D3), renderowanie krótkich komunikatów; testy jednostkowe z tabeli 1.2 -- zrobione: 35 wierszy tabeli = 35 testow
- [x] 2.3 Mutacje (ZASADY 4.4): wyłącz „tylko na początku zdania", zamień domyślną maszynę, pomiń pending - każda ma wywalić test -- zrobione: mutacje 11/11 decide, 8/8 kolejka, 7/7 endpoint
- [x] 2.4 `POST /api/car/say` w `voice_gateway.py`: odmowa -> dialog -> akcja; stare `/api/car/*` bez zmian jako aliasy -- zrobione, pole opcjonalne `zrodlo`
- [x] 2.5 Kolejka FIFO per `(maszyna, projekt)` z dziennikiem i odtworzeniem po restarcie; test restartu -- zrobione (`tools/car_queue.py`)
- [x] 2.6 Odpowiedź asynchroniczna przez `script.odpowiedz_asystenta` dla `queued` -- zbudowane i testowane atrapami; odtwarzanie w aucie czeka na HA 3.4
- [x] 2.7 `car_trail.jsonl`, streszczenie okna do `voice_history` przy „wróć", „gdzie jestem" z `/api/state` + `is_busy` -- zrobione
- [x] 2.8 Adapter `RemoteRelay` (po 2.1); okno zamknięte -> `okna.py`, czekanie na gotowość -- zrobione, zywo sprawdzone; otwieranie zamknietego okna tylko atrapami
- [ ] 2.9 Wykrywanie monitu o zgodę w panelu okna -> komunikat „okno czeka na zgodę" (D8) -- CZESCIOWO: tylko okna na tej maszynie (z domu nie widac panelu)
- [ ] 2.10 ZASADY 2.14: wersja bramki i klon sprawdzone na **obu** maszynach, pomiar z dwóch urządzeń naraz -- CZESCIOWO: praca aktualna; dom ma bramke 286e620e52fe bez /api/car/say, potrzebny `start` + restart voice; test z dwoch urzadzen niezrobiony

- [ ] 2.11 BLAD z e2e 2026-10-29: `przejdz do Car` -> `wroc` -> `gdzie jestem` zwraca okno zamiast rozmowy glownej (mode=window); test sekwencyjny + mutacja; zlecone oknu huba

## 3. HA: okno `HA`

- [ ] 3.1 O2: zbadać zastępczego agenta konwersacji (bez słowa „Claude"); wynik zapisany
- [ ] 3.2 Intent `ClaudeSay` (`claude {pytanie}` + warianty) -> `rest_command.car_say` z `session_id = conversation_id`, `text = pytanie`; odpowiedź = pole `text`
- [ ] 3.3 Stare intenty (Dispatch/Status/Podsumowanie/Otworz/Zamknij/Powtorz) przekierowane na `car_say` z odpowiednim tekstem albo usunięte; `PomocClaude` zaktualizowana o nowe komendy
- [ ] 3.4 Odpowiedź asynchroniczna: `script.odpowiedz_asystenta` przyjmuje wywołanie z bramki dla satelity rozmowy auta
- [ ] 3.5 Deploy `ssh ha-tailscale` + reload, test fraz z tabeli 1.2 przez `conversation.process`

## 2a. Dom i integracja (po raporcie huba 2026-10-29)

- [ ] 2a.1 Dom (DESKTOP-FFSHIOA): `start` + restart `voice` (`monitor/services.py --restart --only voice`), potem `X-Gateway-Version` zgodny z praca (ZASADY 2.14); wykonuje uzytkownik lub okno huba na domu
- [ ] 2a.2 Test z dwoch urzadzen naraz (telefon + auto/komputer, ten sam projekt): kolejka okna wspolna, stany per `session_id` rozdzielne
- [ ] 2a.3 Dialog z oknem HA wymaga atrapy: tabela zaklada HA otwarte na obu maszynach, a e2e wpisalo `drugi` do prawdziwego okna HA (blad z raportu). Runner e2e nie wysyla tresci do okien bez `--live` (patrz 4.1)

## 4. E2E i pomiar (to okno)

- [x] 4.1 (runner gotowy, bez `--live` nie wysyla tresci do prawdziwych okien: `poc/car_dialog_e2e.py`, 5 testów w `test_car_dialog_e2e.py`; na `/api/car/say` jeszcze nieuruchomiony - endpoint nie istnieje, 2026-10-29 połączenie odrzucone). Rozszerzyć `tools/voice_e2e.py` (hub) albo dołożyć `poc/car_dialog_e2e.py` (tu): przebieg „jakie projekty pracują -> przejdź do X -> 3 polecenia -> gdzie jestem -> wróć -> pytanie główne" na prawdziwej ścieżce HA -> bramka -> okno
- [ ] 4.2 PREREJESTRACJA przed pomiarem w aucie (ZASADY 3.3): hipoteza „>= 9/10 przejść do okna kończy się poprawnym projektem i maszyną bez dotykania telefonu", jedna statystyka, warunek NEGATYWU (< 7/10 -> wracamy do gramatyki D2, bez dostrajania po wyniku), czego wynik nie uprawnia (nie mierzy jakości odpowiedzi okna)
- [ ] 4.3 Pomiar w aucie (>= 10 przejść, >= 10 poleceń w oknie, 3 „gdzie jestem", 3 powroty), tabela w `notes/HANDOFF_car_dialog.md`
- [ ] 4.4 Notatka sesji, `python notes/gen_openspec_status.py`, commit i push (ZASADY 2.10)
