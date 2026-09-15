# START — Car_chatGPT_integration

## Ostatnia sesja — 2026-09-15 (sesja 2: host mostu i wdrożenie 24/7)

- **Telefon (Xiaomi Mi 8) odrzucony jako host mostu** — `faster-whisper` nie ma kół na Android-arm64,
  whisper.cpp na SD845 to szacunkowo 15–30 s na 15-sekundowe nagranie wobec **2,1 s zmierzonych** na
  pececie, a Claude Code w Termuksie jest środowiskiem niewspieranym. Mi 8 zostaje dashboardem HA
  i węzłem Tailscale. Host mostu bez zmian: **pecet w pracy**.
- **Gotowy komplet wdrożeniowy `poc/deploy/`** (Windows Pro, lokalny admin): diagnoza `00_check.ps1`,
  zasilanie `01_power.ps1` (monitory 5 min; sen, hibernacja i **unattended sleep** = nigdy), trzy
  zadania Harmonogramu `02_install_tasks.ps1` (most przy starcie systemu na koncie użytkownika
  z zapisanym hasłem, watchdog co 5 min z godzinnym testem głębokim, `git pull --ff-only` co godzinę),
  skrót `Ctrl+Alt+Q` gaszący ekrany, pomiar `check_bridge.ps1`, wycofanie `99_uninstall.ps1`.
  Scenariusz krok po kroku: `poc/deploy/README_PRACA.md`.
- Na tej maszynie uruchomiony wyłącznie `00_check.ps1` (read-only, test poprawności skryptów).
  **Nic nie jest jeszcze wdrożone na pececie w pracy** — to zadania 1.6–1.9.
- **Repozytoria nie muszą leżeć pod wspólnym katalogiem.** `ASK_REPOS` (jawna lista ścieżek, per
  maszyna, z `find_repos.ps1`) albo skan `ASK_ROOT`; repozytoria spoza katalogu roboczego idą do
  `claude -p` przez `--add-dir`.
- **Most sprawdza świeżość przed każdą odpowiedzią**: `git pull --ff-only` we wszystkich repo
  równolegle (brudne pomijane), a do promptu wchodzi blok `STAN DANYCH` ze sha i wiekiem commita.
  Zmierzone: **pull czterech repozytoriów 1,95 s**, czyli mieści się w oknie transkrypcji (2,1 s).
  Pierwsze testy w tym repo: `project_files/python/tests/test_ask_server.py` (7, sprawdzone mutacją).
- Diagram działania (dwie maszyny + oś czasu pytania): https://claude.ai/artifact/MuSA9L3w7rJoWmndXJTuwD

**Aktywne TODO:** `openspec/changes/poc-carplay-command/tasks.md` (6/36). Następne: 1.6–1.9 —
wdrożenie w pracy wg `poc/deploy/README_PRACA.md`; potem 2.7 (skrócenie czasu odpowiedzi)
i grupa 3 (skrót na iPhonie).

## Sesja 2026-09-14 (sesja 1: research + propozycja PoC)

- Research mechanizmów „głos w aucie → własny endpoint”, 23 źródła z datami:
  `notes/research/2026-09-14-mechanizmy-carplay.md`. Dwa ustalenia zmieniają plan:
  **(1) ChatGPT Voice nie obsługuje apps ani MCP** (MCP jest web-only i nie na planie Go), więc ChatGPT
  w CarPlay nie może dziś wywołać niczego; **(2) Siri nie mówi po polsku**, więc polskie polecenie musi iść
  przez dyktowanie iOS z locale `pl_PL`, a nie przez dialog z Siri.
- Utworzona zmiana OpenSpec `poc-carplay-command` (proposal + design + spec + 19 zadań), `validate --strict`
  zielony. Rekomendowana ścieżka PoC: „Hey Siri, Home” → skrót → `Dictate Text` (`pl_PL`) → App Intent HA
  `Assist prompt` → scena w HA → `Speak Text` polskim głosem. Po angielsku tylko fraza budząca.
- Próg zaliczenia zadeklarowany przed pomiarem: ≥ 7/10 udanych prób, mediana czasu do akcji ≤ 10 s,
  ≥ 8/10 poprawnych transkrypcji polskich.
- Drugi research (`notes/research/2026-09-14-chatgpt-jako-wyzwalacz.md`): pomysł „ChatGPT woła mój link,
  tam leci zadanie do Claude'a, odpowiedź wraca pod linkiem" jest poprawny, ale **aplikacja ChatGPT
  w trybie głosowym nie ma wspieranego sposobu wołania webhooków** i nikt tego nie opublikował jako
  działającego. Rozmowa z ChatGPT z narzędziami jest dziś możliwa, gdy ChatGPT jest **modelem** w Assist
  (OpenAI Conversation) — skrypty HA stają się wtedy narzędziami modelu, a jeden z nich jest mostem do
  `claude -p`. Dosłowna wersja została eksperymentem E1 (zadania 4.3–4.4).
- **Przestawienie celu PoC (decyzja użytkownika 2026-09-14)**: chodzi o rozmowę z project_monitorem
  („jakbym gadał w oknie Claude Code"), a nie o sterowanie domem. Mózgiem jest **Claude** przez nowy
  endpoint `POST /api/ask` w project_monitorze; OpenAI API nie wchodzi, bo subskrypcja Go i tak nie
  podłącza się do HA. Siri zostaje wyłącznie wyzwalaczem dwóch angielskich słów, a **polską mowę
  nagrywa skrót i przepisuje Whisper** — nie Siri i nie dyktowanie Apple.
- Zmiana OpenSpec przepisana pod ten cel, a **most działa i jest zmierzony**: `poc/ask_server.py`
  przyjmuje nagranie albo tekst, transkrybuje po polsku lokalnym Whisperem, pyta `claude -p` z
  narzędziami tylko do odczytu i oddaje czysty tekst do przeczytania głosem. Pierwsze liczby:
  transkrypcja 2,1 s przy ciepłym modelu, pełna pętla od 13,8 do 34,5 s, odpowiedzi merytorycznie
  poprawne. **Wąskim gardłem jest Claude czytający pliki, nie głos** — próg 15 s jeszcze nietrafiony,
  naprawa w zadaniu 2.7. Szczegóły i instrukcja skrótu na iPhonie: `notes/HANDOFF_most_pytan.md`.
- Maszyna docelowa: **stale włączony pecet w pracy** w tailnecie; RPi z HA tego nie uciągnie.

**Aktywne TODO:** `openspec/changes/poc-carplay-command/tasks.md` (6/32). Następne: 1.3 — uruchomić most
na pececie w pracy; grupa 3 — zbudować skrót na iPhonie; 2.7 — skrócić czas odpowiedzi.

## Czym jest ten projekt

Głos w samochodzie (ChatGPT w CarPlay na iPhonie) ma uruchamiać operacje na własnej infrastrukturze:
Home Assistant, GitHub, komputery przez Tailscale, Claude Code. **Główny sens i uzgodniona architektura
są w `rozmowa_ChatGPT_CarPlay_integracje.pdf` w korzeniu repo** — to zapis rozmowy z ChatGPT, który
kończy się propozycją: ChatGPT jako „kokpit głosowy”, jeden własny **Command Center** (API / webhook / MCP)
jako „ręce” z whitelistą operacji i logiem, Claude do cięższej pracy z kodem.

Kluczowy wniosek z PDF (str. 2–3): **nie budować nic, dopóki nie ma jednego proof of concept** —
„Hej ChatGPT, uruchom mi X” → operacja na infrastrukturze → odpowiedź głosem. Najpierw trzeba znaleźć
mechanizm, którym ChatGPT Voice na iPhonie może wywołać własny endpoint (kandydaci: Apple Shortcuts / Siri
→ API; webhook z mechanizmu dostępnego w ChatGPT; własna aplikacja iOS z CarPlay; Home Assistant jako
pośrednik). Dopiero po potwierdzeniu PoC — reszta.

## Co już istnieje i można użyć

- **Home Assistant** na RPi 4 (HA OS), Tailscale `100.117.49.43`, dodatek `project_monitor` (FastAPI) jako
  wzór add-onu z API i Ingress: `D:\claude_projects\project_integration`.
- Repo `HA` (konfiguracja HA, automatyzacje, dashboardy) — `D:\claude_projects\HA`.
- Komputery w tailnecie z Claude Code; hooki monitora w każdym repo (`monitor/heartbeat.py`).
- Aplikacja HA na iPhone (powiadomienia, webhooki `notify`).

## Pierwsza sesja — co ma się wydarzyć po „start”

1. Przeczytać ten plik i **cały PDF** (`pdftotext -layout rozmowa_ChatGPT_CarPlay_integracje.pdf -`).
2. Research (WebSearch, źródła z datami): jakie dziś mechanizmy pozwalają ChatGPT Voice / CarPlay na iPhonie
   wywołać zewnętrzny endpoint — ChatGPT Apps/MCP w planie Go, Apple Shortcuts + Siri z aplikacją ChatGPT,
   Home Assistant Assist w CarPlay, webhooki HA. Dla każdej ścieżki: co działa w samochodzie bez dotykania
   telefonu, co wymaga planu wyżej, co wymaga własnej aplikacji iOS.
3. Utworzyć zmianę OpenSpec `poc-carplay-command` (`/opsx:propose`): proposal z rekomendacją **jednej**
   ścieżki PoC (reguła 7.2: rekomendacja, nie katalog), design z diagramem przepływu, tasks z krokami PoC
   zakończonymi pomiarem: „polecenie głosowe w samochodzie → akcja w HA (np. scena) → odpowiedź głosem”,
   czas od słowa do akcji w sekundach, liczba prób udanych / wszystkich.
4. Notatka sesji `notes/sesje/2026-MM-DD-sesja.md`, aktualizacja tego pliku (reguła 1.1), STATUS.md.

Non-goals na start: własny Command Center w kodzie, MCP, integracje GitHub/Claude Code — dopiero po PoC.

## Środowisko

- Branch roboczy: `main`
- Uruchomienie: brak kodu (PoC zdecyduje o stacku; kandydat: Python/FastAPI jak w `project_integration`,
  wdrożenie jako dodatek HA albo kontener na komputerze w tailnecie)
- Monitor: `~/.claude/monitor.env` już jest na tej maszynie; hooki działają od pierwszej sesji.
