# Raport sprintu CarPlay/HA — 2026-10-12 (pętla autonomiczna 4h)

> Dla rannej lektury. Wszystko gotowe do testu w aucie.

## Co masz w aucie — 11 komend głosowych

Mówisz w aucie przez **HA Assist** (ikona HA w CarPlay → kafelek Assist). Słyszysz
**swoim głosem Sznuk**.

| co mówisz | co się dzieje |
|---|---|
| **Claude test** / Claude ping | ping całej pętli; „pętla działa" |
| **Claude pomoc** / Claude menu | recytacja listy projektów i form fraz |
| **Claude status** / Claude stan | ile projektów, ile pracuje, ile otwartych zadań, niewypchnięte |
| **Claude otwórz <projekt>** | otwiera okno w tmux (idempotentne) |
| **Claude podsumowanie <projekt>** / Claude co z <projekt> | stan konkretnego projektu |
| **Claude do okna <projekt>, <polecenie>** | wrzuca polecenie do działającego Claude Code |
| **Claude kontynuuj <polecenie>** | sticky — kolejne polecenie bez nazwy (10 min TTL) |
| **Claude zapisz zadanie <tekst>** | zapisuje TODO do pliku |
| **Claude moje todo** / Claude ostatnie zadania | recytuje 5 ostatnich TODO |
| **Claude zamknij** / Claude koniec | kasuje sticky sesję |
| **Claude powtórz** / Claude nie słyszałem | powtarza ostatnie Głosowo |

Plus **12-ty intent**: **„Claude metryki"** / Claude ile używałeś → `ostatnie 24h: 122 wywolan,
dispatch 32, poc 30, status 13`. **PomocClaude** zaciąga listę projektów dynamicznie z
`/api/car/projekty` (nie hardcoded).

## Co było naprawione

1. **TTS brzmi twoim głosem** (nie Piperem) — na WSZYSTKICH komendach, nie tylko ZapytajClaude.
   HA commit d025d8e przełączył `script.zapowiedz` na `tts.speak` z serwerem prywatnych głosów.
2. **„Claude do okna X" nie trafia w `turn_on X`** — encje `input_boolean.pm_*` zmieniły nazwy
   na „PM <nazwa>" w HA entity_registry. `wlacz project_integration` → `no_match`.
3. **Fuzzy „car integration" działa** — nowy 4-ty tier w `okna.resolve` (token-match
   dla ≥ 2 słów rozstrzelonych w nazwie).

## Liczby

- **12 endpointów bramki**, **12 intentów HA** (wszystkie podpięte, w tym MetrykiClaude
  i dynamic PomocClaude)
- **89 testów PI** (zielony pytest), **15/15 self-test** z komputera (~38 s cykl)
- **23 wzorce odmów** pisujących (było 11); 12 nowych testów parametrycznych
- **15 commitów** łącznie (10 PI, 5 Car), wszystkie **pushed**
- **121 wywołań** endpointów `/api/car/*` w ciągu 24 h (dispatch 32, poc 30, status 13…)
- **HANDOFF_car_endpoints.md** — 450+ linii dokumentacji ↔ kontrakt bramka ↔ HA
- **3 PDFy ściągi** wysłane mailem (v1, v2, v3) wraz z aktualizacjami

## Ryzyka pozostałe

1. **Pomiar w aucie czeka** — serie C wg prerejestracji, ≥ 10 prób, mediana ≤ 20 s.
   Potrzebne po jeździe żeby zarchiwizować `carplay-okna-projektow`.
2. ~~**Dynamiczna lista projektów w PomocClaude**~~ — **zrobione** (HA commit 841e8a5),
   `PomocClaude` zaciąga listę z `/api/car/projekty` zamiast hardcoded.
3. ~~**MetrykiClaude**~~ — **zrobione** (HA commit 841e8a5), 6/6 fraz łapie
   („Claude metryki", „Claude ile używałeś", „Claude liczby").
4. **Diagnostyczne `/api/car/test-{audio,text}`** do usunięcia po pomiarze (task 7.1).

## Jak sprawdzić że wszystko działa — sanity check z komputera

```bash
python D:/claude_projekty/Car_chatGPT_integration/poc/car_selftest.py
# -> 15/15 PASS w ~38s
```

## Jak sprawdzić że wszystko działa — w aucie

1. Jedź do auta, CarPlay USB, silnik.
2. Dotknij HA → kafelek Assist.
3. **„Claude test"** → ma odpowiedzieć „pętla działa" twoim głosem.
4. **„Claude status"** → recytacja liczb.
5. **„Claude do okna car integration, pokaż tasks"** → polecenie leci do mnie, odpowiedź.
6. **„Claude powtórz"** → powtórka.
7. Wracasz, mówisz co nie zadziałało. Logi w `voice_gateway.log` wszystko złapały.

## Pliki do przejrzenia

- **Pętla rejestr**: `project_files/run_files/petla_2026-10-12/petla_rejestr.md`
- **Notatka sesji**: `notes/sesje/2026-10-12-carplay-ha-pilny-sprint.md`
- **HANDOFF endpoint**: `notes/HANDOFF_car_endpoints.md`
- **HANDOFF Shortcut PoC**: `notes/HANDOFF_carplay_okna.md`
- **PDF v3 ściąga**: w mailach (meow@mat.umk.pl → michal.chlebiej@gmail.com)
- **OpenSpec zmiana**: `openspec/changes/carplay-okna-projektow/`
- **Self-test**: `poc/car_selftest.py`

## Decyzja do podjęcia

**Czy archiwizować zmianę `carplay-okna-projektow`** (`/opsx:archive`), czy czekać
na pomiar jazdowy serii C? Rekomenduję poczekać — prerejestracja istnieje, pomiar
blokuje warunek NEGATYWU wg `tasks.md 6.1`.
