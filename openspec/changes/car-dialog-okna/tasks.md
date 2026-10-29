## 1. Plan i kontrakt (to okno)

- [x] 1.1 proposal, design (D1-D9), spec `car-dialog` - 2026-10-29
- [x] 1.2 Tabela scenariuszy e2e `notes/car_dialog_scenariusze.md`: wypowiedź -> oczekiwany `outcome`/`state`/początek `text` (>= 30 wierszy, w tym graniczne z R1); to jest wspólny kontrakt dla testów huba i e2e
- [x] 1.3 Zlecenie okna `project_integration` (grupa 2) i okna `HA` (grupa 3) wysłane; wyslane przez send_task.py 2026-10-29 (oba OK, bridge GEIH38C), godzina w notatce sesji

## 2. Hub: `project_integration` (okno huba)

- [ ] 2.1 O1: zmierzyć, czy relay drugiej maszyny zwraca odpowiedź okna (`/task` jednokierunkowy?); wynik w `notes/HANDOFF_car_dialog.md`; jeśli brak - dołożyć `GET /reply`
- [ ] 2.2 `tools/car_dialog.py`: czyste `decide(state, text, world)`, parser komend (D2), wybór maszyny (D3), renderowanie krótkich komunikatów; testy jednostkowe z tabeli 1.2
- [ ] 2.3 Mutacje (ZASADY 4.4): wyłącz „tylko na początku zdania", zamień domyślną maszynę, pomiń pending - każda ma wywalić test
- [ ] 2.4 `POST /api/car/say` w `voice_gateway.py`: odmowa -> dialog -> akcja; stare `/api/car/*` bez zmian jako aliasy
- [ ] 2.5 Kolejka FIFO per `(maszyna, projekt)` z dziennikiem i odtworzeniem po restarcie; test restartu
- [ ] 2.6 Odpowiedź asynchroniczna przez `script.odpowiedz_asystenta` dla `queued`
- [ ] 2.7 `car_trail.jsonl`, streszczenie okna do `voice_history` przy „wróć", „gdzie jestem" z `/api/state` + `is_busy`
- [ ] 2.8 Adapter `RemoteRelay` (po 2.1); okno zamknięte -> `okna.py`, czekanie na gotowość
- [ ] 2.9 Wykrywanie monitu o zgodę w panelu okna -> komunikat „okno czeka na zgodę" (D8)
- [ ] 2.10 ZASADY 2.14: wersja bramki i klon sprawdzone na **obu** maszynach, pomiar z dwóch urządzeń naraz

## 3. HA: okno `HA`

- [ ] 3.1 O2: zbadać zastępczego agenta konwersacji (bez słowa „Claude"); wynik zapisany
- [ ] 3.2 Intent `ClaudeSay` (`claude {pytanie}` + warianty) -> `rest_command.car_say` z `session_id = conversation_id`, `text = pytanie`; odpowiedź = pole `text`
- [ ] 3.3 Stare intenty (Dispatch/Status/Podsumowanie/Otworz/Zamknij/Powtorz) przekierowane na `car_say` z odpowiednim tekstem albo usunięte; `PomocClaude` zaktualizowana o nowe komendy
- [ ] 3.4 Odpowiedź asynchroniczna: `script.odpowiedz_asystenta` przyjmuje wywołanie z bramki dla satelity rozmowy auta
- [ ] 3.5 Deploy `ssh ha-tailscale` + reload, test fraz z tabeli 1.2 przez `conversation.process`

## 4. E2E i pomiar (to okno)

- [ ] 4.1 Rozszerzyć `tools/voice_e2e.py` (hub) albo dołożyć `poc/car_dialog_e2e.py` (tu): przebieg „jakie projekty pracują -> przejdź do X -> 3 polecenia -> gdzie jestem -> wróć -> pytanie główne" na prawdziwej ścieżce HA -> bramka -> okno
- [ ] 4.2 PREREJESTRACJA przed pomiarem w aucie (ZASADY 3.3): hipoteza „>= 9/10 przejść do okna kończy się poprawnym projektem i maszyną bez dotykania telefonu", jedna statystyka, warunek NEGATYWU (< 7/10 -> wracamy do gramatyki D2, bez dostrajania po wyniku), czego wynik nie uprawnia (nie mierzy jakości odpowiedzi okna)
- [ ] 4.3 Pomiar w aucie (>= 10 przejść, >= 10 poleceń w oknie, 3 „gdzie jestem", 3 powroty), tabela w `notes/HANDOFF_car_dialog.md`
- [ ] 4.4 Notatka sesji, `python notes/gen_openspec_status.py`, commit i push (ZASADY 2.10)
