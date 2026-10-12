# HANDOFF — voice_gateway endpointy /api/car/*

## 2026-10-12: endpoint `/api/car/stop` — znane ograniczenia (KRYT 1 z Z25)

**Nie-bug, nie fix-in-place. Decyzja projektowa, wymaga nowego proposal/design.**

Co jest nie tak (zidentyfikowane przez code review 2 w pętli profesor-student Z25):

1. **Routing tmux pane**: `send-keys -t =<session>:` idzie do **aktywnego okna sesji**, nie konkretnego pane. Jeśli sesja ma wiele okien (co jest regułą w sesjach projektów Claude Code z 1 oknem per pane projektu i dodatkowymi), Ctrl-C poleci do zupełnie innego pane niż ten, który user miał na myśli. **Zmierzyć**: ile z 22 sesji projektów ma > 1 pane w typowym użyciu — jeśli zero, routing jest akademickim problemem; jeśli kilka, trzeba doprojektować `/stop?pane=X&window=Y`.

2. **Signal handling `claude -p`**: Claude Code ma własny signal handler w trybie interaktywnym. Pojedyncze SIGINT (`Ctrl-C`) czyści prompt / anuluje readline, **nie** zabija generowania ani nie przerywa trwającego tool-use. Pomiar Z24 (10 prób, `pane_alive_after=False`) dał wynik tylko dlatego, że pane zawierał `sleep 300` jako jedyny proces — tam SIGINT faktycznie zabija. **Zmierzyć**: ile razy SIGINT trzeba posłać do `claude -p` w generowaniu żeby przerwać; może potrzebny `C-c C-c` z opóźnieniem, może `q`, może nic z zewnątrz nie pomoże i trzeba REST do samego Claude Code.

3. **Komunikat „stopnieto X" kłamie**: endpoint zwraca ten tekst niezależnie od tego, czy pane coś robił i czy SIGINT cokolwiek zmienił. **Fix**: diff `capture-pane` przed i po, raportować „SIGINT wysłany, pane się nie zmienił" vs „pane zareagował". Albo zmienić semantykę na „nie wiem, co stopnieto — wysłałem SIGINT".

**Nie dotykać endpointu bez nowego proposal.** Fix in-place w 65 min w nocy z 2 na 3 października daje gwarantowany półprodukt. Decyzja projektowa idzie przez OpenSpec (`proposal.md` + `design.md` + `tasks.md`), nie przez pętlę profesor-student.

**Status Z25 na dziś**: zmierzone, zapisane, zostawione. Code produkcyjny bez zmian (`git diff tools/voice_gateway.py` puste po przywróceniu mutacji — zweryfikowane mechanicznie).

**Linki**: `openspec/changes/carplay-okna-projektow/tasks.md` 2c.12 (prerejestracja), 2c.13 (negatyw Z25.M2), wpis WYMAGA PROJEKTU.

## 2026-10-12: KRYT 2 — `outcome="timeout"` dla rc!=0 bez timeoutu

Fix lokalny, 5 min + 1 pytest z mutacją. Nie zrobiony w Z25 na wyraźną decyzję profesora: „nie poprawiaj przy okazji niczego z code review poza krytycznym". KRYT 2 to lokalny fix, nie krytyczne pod warunkiem że user wie, że „timeout" w tym endpoincie znaczy albo prawdziwy timeout, albo błąd tmux. Opisane w `tasks.md` jako „FIX lokalny z warunkiem akceptacji".

## Wnioski z Z25 dla pozostałych endpointów `/api/car/*`

**Reguła 4.4 „testy sprawdzone mutacją" była w tym repo spełniona nominalnie** (testy istniały, nazwa pytest nazywała porażkę), **nie merytorycznie** (mutacja ich nie ruszała dla sukces-branche semantyki `send-keys` → self-testu live złapał, pytest nie). Dla pozostałych endpointów warto osobno zmierzyć:

- Czy pytest `test_car_dispatch.py` łapie mutacje w semantyce `_car_dispatch` (`type_into` / `capture` / `extract_reply`)?
- Jeśli nie — self-test live jest jedyną linią obrony, i to **nie są** testy jednostkowe, tylko integracyjne.

To nie jest zadanie na dziś. Zapis dla ciągłości.
