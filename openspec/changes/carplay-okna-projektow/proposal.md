## Why

PoC `poc-carplay-command` (zmiana w tym samym repo) zakłada jedno wywołanie `claude -p` w trybie
tylko do odczytu — odpowiada na pytanie „co się dzieje z projektem X", ale **nie prowadzi rozmowy
z uruchomionym Claude Code w konkretnym projekcie**. Tymczasem w `project_integration` powstała
infrastruktura do otwierania okien projektów w tmux (`tools/okna.py`, ttyd 7681, `cli_bridge`),
rozmawiania z nimi głosem z telefonu i Home Assistanta (`monitor/voice_gateway.py`, `Glosowo:`),
oraz mapa 22 projektów (`~/.claude/monitor_repos.env`). Jedno ogniwo nie istnieje: **nie da się
z CarPlay wybrać projektu głosem i wysłać do niego kolejnych poleceń jak w zwykłym oknie**.
Decyzja użytkownika 2026-10-12: zbudować to teraz, bo wszystkie trzy cegły (mapa, okna, głos)
są już zmierzone i działają z telefonu — brakuje tylko mostka Siri Shortcuts i rejestru
„aktywne okno dla sesji w aucie".

## What Changes

- Siri Shortcut „Projekt" (iOS 17+) nagrywa polski prompt → POST do nowego endpointu
  `/api/car/command` w bramce głosowej → `Record Audio` → odtwarza zwrócone `audio/mpeg`.
  **Siri widzi dwa słowa po angielsku** („Projekt" jako nazwa skrótu), całe polskie zdanie
  idzie do Whispera — tak samo jak w `poc-carplay-command`.
- Nowy endpoint `POST /api/car/command` w `project_integration/monitor/voice_gateway.py`:
  (1) Whisper → tekst, (2) parser „projekt X: <polecenie>" (prefiks lub pierwsze słowa) →
  `okna.resolve()` dla fuzzy match nazwy, (3) `tmux send-keys` do istniejącej sesji projektu
  albo odmowa „nie ma takiego okna, otworzyć?" (idempotentne — otwarcie okna to osobna
  pozytywna odpowiedź użytkownika), (4) nasłuch na `Glosowo:` w output tmux → TTS →
  `audio/mpeg` jako body odpowiedzi.
- **Rejestr aktywnej sesji CarPlay** (`~/.claude/carplay_sessions.json`): klucz = `session_id`
  z Siri Shortcut (UUID z nagłówka), wartość = nazwa aktywnego projektu + czas ostatniej
  interakcji. Po powiedzeniu samego „projekt X" (bez polecenia) sesja się ustawia; kolejne
  komendy bez prefiksu idą tam. Wygasa po 10 minutach ciszy (odczyt z HANDOFF car-session).
- **Progi akceptacji wbudowane w parser**:
  - `okna.resolve()` zwraca listę kandydatów; przy jednoznacznym dopasowaniu → wykonanie;
    przy dwuznaczności → `Glosowo: który projekt — X czy Y?`; przy braku → `Glosowo:
    nie znalazłem projektu Z`. Nic nie wysyłamy do tmux dopóki jedno okno nie wygrało.
  - Timeout odpowiedzi: 30 s na pojawienie się linii `Glosowo:` w output tmux; po tym czasie
    `Glosowo: pracuje jeszcze — zapytam za chwilę` i oznaczenie sesji „pending" (nie
    przechwytywane kolejne).
  - Odmowa poleceń pisujących w stylu `rm`, `git push`, `sudo` **po stronie parsera CarPlay**
    (dodatkowo do i tak czujnego Claude). Powód: w aucie użytkownik nie potwierdzi dialogu.
- **PoC-first**: pierwsze zadanie w `tasks.md` to pomiar, czy Siri Shortcuts w CarPlay potrafi
  odebrać `audio/mpeg` z HTTPS endpointu w tailnecie i odtworzyć przez głośnik auta — bez tego
  cała reszta nie ma sensu. Mierzone na postoju, 3 próby po polsku, zapis do
  `notes/HANDOFF_carplay_okna.md`.

## Capabilities

### New Capabilities
- `car-window-dispatch`: polecenie głosowe z CarPlay wybiera projekt z mapy
  `monitor_repos.env`, kieruje prompt do istniejącej sesji tmux tego projektu i zwraca
  `Glosowo:` jako audio do głośnika auta; definiuje parser nazwy, rejestr aktywnej sesji,
  progi akceptacji, timeout i warunki odmowy.

### Modified Capabilities
<!-- brak — openspec/specs/ jest pusty; capability `voice-command-ha-poc` z poc-carplay-command
     nie jest jeszcze zarchiwizowana i opisuje inny przepływ (one-shot `claude -p`, read-only),
     więc nowa capability car-window-dispatch stoi obok, nie modyfikuje jej. -->

## Impact

- **project_integration** (`monitor/voice_gateway.py`): nowy endpoint `/api/car/command`;
  reuse `okna.resolve()`, `SPOKEN_MARK`, `speak()`, `tmux send-keys` z `cli_bridge_reap.sh`.
  **Nowe pliki tylko wtedy, gdy trzeba** — parser prefiksu i rejestr sesji mogą żyć
  w `voice_gateway.py` dopóki nie urosną.
- **Car_chatGPT_integration** (to repo): plik `.shortcut` lub instrukcja krok-po-kroku
  w `notes/HANDOFF_carplay_okna.md`; prerejestracja i tabela pomiarów PoC; skrypt pomiarowy
  w `poc/` reużywa `poc/deploy/check_bridge.ps1` z `poc-carplay-command`.
- **Zero zmian w HA, HomeAssistant Companion, iPhone poza instalacją skrótu.** Nie dotyka
  potoku głosowego HA ani Assist.
- **Zero zmian w `monitor_repos.env`** — mapa już istnieje i jest utrzymywana przez
  `project_integration/tools/ready.py`.
- **Poza zakresem**: wywoływanie `/opsx:apply` z auta (ryzyko utraty kontekstu rozmowy
  z Claude), rozmowa wieloturowa z pamięcią kontekstu po stronie bramki (polegamy na stanie
  samej sesji Claude w tmux), nowe projekty / repozytoria (dopisanie do mapy jest osobnym
  procesem — ZASADY 9).
