# Scenariusze dialogu auta (kontrakt dla testów huba i e2e)

Zmiana: `openspec/changes/car-dialog-okna`. Świat testowy: projekty `Car_chatGPT_integration`, `HA`,
`project_integration`, `RibnXtr2026`, `vESSA---vessel-analysis`; maszyny `praca` (domyślna), `dom`.
Okna otwarte: `Car` tylko praca; `HA` praca i dom; `project_integration` tylko praca; reszta zamknięta.
Kolumna „stan przed" -> „stan po"; `main` = rozmowa główna, `W(p,m)` = okno p na maszynie m.

| # | stan przed | wypowiedź | outcome | stan po | tekst zaczyna się / zawiera |
|---|---|---|---|---|---|
| 1 | main | jakie projekty teraz pracują | answered | main | lista projektów ze stanem `working` |
| 2 | main | przejdź do projektu car integration | moved | W(Car,praca) | „Car", „w pracy" |
| 3 | main | przejdź do HA | pending | main + pending(machine) | „w pracy czy w domu" |
| 4 | pending(machine,HA) | w pracy | moved | W(HA,praca) | „HA" |
| 5 | pending(machine,HA) | pierwszy | moved | W(HA,praca) | kolejność opcji = praca, dom |
| 6 | main | przejdź do HA w domu | moved | W(HA,dom) | bez pytania |
| 7 | main | przejdź do HA na komputerze w pracy | moved | W(HA,praca) | bez pytania |
| 8 | main | do okna project integration | moved | W(project_integration,praca) | |
| 9 | main | przejdź do rib | moved | W(RibnXtr2026,praca) | okno zamknięte: „otwieram" |
| 10 | main | przejdź do projektu który nie istnieje | missing | main | „nie znam" |
| 11 | main | przejdź do vessel | moved lub pending | | niejednoznaczność = pending(project) |
| 12 | pending(project) | drugi | moved | W(drugi,...) | |
| 13 | pending(machine) | pogoda | answered | main, pending skasowany | inna wypowiedź anuluje pytanie |
| 14 | W(Car,praca) | dodaj test do parsera | queued lub answered | W(Car,praca) | polecenie w kolejce okna Car |
| 15 | W(Car,praca), okno zajęte | a potem sprawdź testy | queued | W(Car,praca) | „po bieżącym" |
| 16 | W(Car,praca) | gdzie jestem | where | W(Car,praca) | „Car", „w pracy", stan okna |
| 17 | main | gdzie jestem | where | main | „rozmowie głównej" |
| 18 | W(Car,praca) | gdzie pracujemy | where | bez zmian | jak 16 |
| 19 | W(Car,praca) | wróć | moved | main | „rozmowa główna"; wpis w historii głównej |
| 20 | W(Car,praca) | rozmowa główna | moved | main | |
| 21 | W(Car,praca) | przejdź do HA w domu | moved | W(HA,dom), trail=[Car] | |
| 22 | W(HA,dom), trail=[Car] | wróć do poprzedniego | moved | W(Car,praca) | |
| 23 | W(Car,praca) | jakie projekty pracują | answered | W(Car,praca) | zostaje w oknie, odpowiedź z monitora |
| 24 | W(Car,praca) | powiedz oknu wróć do pierwszego akapitu | queued | W(Car,praca) | do okna idzie „wróć do pierwszego akapitu" |
| 25 | W(Car,praca) | wróć do pierwszego akapitu | queued | W(Car,praca) | **nie** komenda: „wróć do" + brak okna docelowego = tekst do okna |
| 26 | W(Car,praca) | powtórz | answered | bez zmian | ostatnie Glosowo |
| 27 | main | git push origin main | refused | main | „w aucie tego nie zrobię" |
| 28 | W(Car,praca) | zrób rm -rf na katalogu | refused | W(Car,praca) | nic nie trafia do okna |
| 29 | main | zamknij okno | answered | main | „nie ma otwartego okna" |
| 30 | W(Car,praca) | zamknij okno | answered | main | „zamykam" lub „zostawiam otwarte" (decyzja huba, zapisana) |
| 31 | W(Car,praca), cisza 30 min | dodaj test | queued | W(Car,praca) | zaczyna się „Jesteś nadal w oknie" |
| 32 | W(Car,praca), cisza 5 h | dodaj test | answered | main | „Poprzednie okno wygasło" (stan > 4 h) |
| 33 | main, praca offline | przejdź do Car | pending | main + pending(machine) | „komputer w pracy nie odpowiada" |
| 34 | W(Car,praca), okno bez monitoru | gdzie jestem | where | bez zmian | „nie widzę stanu okna" (brak danych wymieniony) |
| 35 | main | przejdź do | missing lub pending | main | „do którego projektu?" |

Wiersz 25 jest testem R1 (słowo-klucz połknąłby zdanie). Wiersze 13, 24, 31, 32 testują stan, nie gramatykę.
