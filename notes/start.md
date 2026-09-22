# START — Car_chatGPT_integration

## Ostatnia sesja — 2026-09-22 (sesja 4: weryfikacja ChatGPT Voice + wariant „Monitor GPT")

- **PDF `podsumowanie_voice_claude_carplay.pdf` zweryfikowany u źródeł — jego rekomendacja nie
  prowadzi do ChatGPT Voice.** `osaighi/talk-to-claude-code` (istnieje, 31 commitów) jest zbudowany
  pod **Grok Voice** na CarPlay, bo Grok ma „Bring Your Own MCP"; `fireishott/Herald` jest własną
  aplikacją iOS i **zarchiwizowany 2026-08-06**; cytat o zgłoszeniu w `anthropics/claude-ai-mcp`
  **niepotwierdzony** (DO WERYFIKACJI). Szczegóły i linki:
  `notes/research/2026-09-22-chatgpt-voice-weryfikacja.md`.
- **ChatGPT jest w CarPlay natywnie od marca 2026** (iOS 26.4+), ale bez słowa budzącego i bez
  możliwości sterowania czymkolwiek, a **tryb głosowy nadal nie obsługuje apps/konektorów/MCP**
  (pomoc OpenAI + otwarty wątek deweloperski). Ustalenie sesji 1 trzyma się bez zmian.
- **Zrealizowany wariant C skrótu — „Monitor GPT"**: most oddaje pod `?style=facts` zwięzłe fakty
  (do sześciu linii, 1500 znaków) zamiast zdania do przeczytania, a zdanie dla kierowcy układa
  akcja **Ask ChatGPT** w Skrócie. To **jedyna droga, żeby w pętli siedział głos ChatGPT** —
  ręce ma Skrót, nie model. Kroki: `notes/HANDOFF_most_pytan.md`. Domyślne zachowanie mostu
  **bez zmian** (ZASADY 4.9).
- **Pomiaru jeszcze nie ma, prerejestracja jest** (zadanie 3.8): jedno porównanie, warunek negatywu
  zadeklarowany z góry — mediana dłuższa o > 4 s bez poprawy zrozumiałości ⇒ wariant odrzucony
  i nie strojony. Świadomie trzymane osobno od trzech porównań z 5.1 (wielokrotność, ZASADY 5.4).
- Testy: **28 zielonych**, mutacja `for_facts` złapana przez dwa testy.

- **Decyzja użytkownika: rozmowa ciągła jest ważniejsza niż to, że to ma być ChatGPT.** Nowa zmiana
  OpenSpec **`voice-grok-front`** (24 zadania, `validate --strict` zielony): front to **Grok Voice**
  (CarPlay od maja 2026, tryb głosowy sięga po własne konektory MCP i odpytuje w pętli), mózgiem
  zostaje orchestrator z `project_integration`.
- **Nie budujemy mózgu drugi raz.** Serwer MCP ma być cienką warstwą przed `POST /api/agent/chat` —
  zero własnego promptu, zero `claude -p`, zero drugiej listy repozytoriów (test w zadaniu 2.4).
  `ask_core.py`, `voice_gateway.py` i `execute_worker.py` już istnieją i działają.
- **Remote Control ≠ to samo.** Podłącza żywą lokalną sesję do claude.ai/code i aplikacji Claude
  (Pro/Max/Team/Enterprise), ale **bez API i bez CarPlay** — telefon w ręku, nie auto. Do żywego
  okna interaktywnego **z CLI nie da się wejść** (spike 2026-09-17); `claude -p --resume` tylko
  przy oknie bezczynnym.
- **Prawdziwa cena: most musi wyjść za Tailscale Funnel**, czyli z prywatnego staje się publiczny.
  Stąd bramki grupy 3 przed włączeniem: limit tempa, log, zapis domyślnie wyłączony i wyłącznie
  przez `execute_worker`, potwierdzenie głosem.

**Aktywne TODO:** `voice-grok-front` 1.1–1.5 (potwierdzić plan Grok-a, przeczytać
`talk-to-claude-code`, zmierzyć orchestrator, uzupełnić `live_sessions.py`);
`poc-carplay-command` 3.8–3.9 (pomiar wariantu C), 1.6–1.9 (wdrożenie na pececie w pracy),
2.7 (skrócenie czasu odpowiedzi), 6.1–6.2 (E1, wciąż nierobiony); `voice-intent` 5.5, 5.6, 6.3.

## Ostatnia sesja — 2026-09-16 (sesja 3: warstwa intencji mostu głosowego)

- **Most rozumie już nie tylko pytania, ale i zamiar.** Nowa zmiana OpenSpec `voice-intent`
  (proposal + design + spec + 29 zadań, `validate --strict` zielony) i jej implementacja:
  transkrypcja → struktura `{v, intent, repo, repo_reason, text, limit_zdan}` → dopiero potem model.
  Zaimplementowany wyłącznie `intent: ask`; `note` i `queue` są rozpoznawane i **odrzucane zdaniem
  po polsku z kodem 200** (skrót czyta treść — kod błędu skończyłby się ciszą).
- **Nazwa projektu rozpoznawana z przekręconej mowy.** `poc/aliases.json` to **dane**, nie kod:
  nowy projekt = jeden wpis. Dopasowanie po n-gramach słów przez `difflib`, próg z pliku danych,
  nazwy kanoniczne z `~/.claude/monitor_repos.env` (bez drugiej listy repozytoriów).
- **Zmierzone (prerejestracja 3.3 zapisana przed przebiegiem):** trafność rozpoznania repozytorium
  **83,9%** (26/31 wypowiedzi z nazwanym projektem; hipoteza ≥ 80%), fałszywe trafienia **2,3%**
  (1/43; warunek ≤ 10%). Próg `min_ratio` = 0,82 zadeklarowany z góry, jedno porównanie, nie
  strojony po wyniku. **Wynik nie mówi nic o mowie w jadącym aucie** — 41 z 43 wypowiedzi napisano
  przy biurku (zadanie 5.6: nagrać prawdziwe).
- **Zawężenie zakresu do jednego repo NIE przyspiesza odpowiedzi** (prerejestracja 5.2, wynik
  negatywny zgodnie z zadeklarowanym warunkiem): mediana 14,0 s wobec 14,2 s przy wszystkich repo,
  n=5+5, różnica tonie w rozrzucie 11,8–25,2 s. Zawężenie zostaje jako ochrona przed odpowiedzią
  z cudzego drzewa i **nie jest** opisywane jako przyspieszenie. Przy okazji: sam `claude -p` ma
  medianę **14,1 s** — to liczba do zadania 2.7, i kolejne potwierdzenie, że wąskim gardłem jest
  model czytający pliki, nie głos.
- 10/10 wywołań w tym przebiegu zaczęło odpowiedź od nazwy repozytorium — decyzja „nazwij repo
  zamiast pytać o potwierdzenie" działa w praktyce.
- Testy: **25 zielonych**, sześć mutacji sprawdzonych i każda złapana.

**Aktywne TODO:** `openspec/changes/voice-intent/tasks.md` (5.5, 5.6, 6.3) oraz bez zmian
`poc-carplay-command` 1.6–1.9 i 2.7; `ask-core-client` czeka na `monitor/ask_core.py`.

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
