# START — Car_chatGPT_integration

## Ostatnia sesja — 2026-09-14 (sesja 0: inicjalizacja)

- Repo zainicjalizowane, paczka `project_integration` wgrana (ZASADY v1.4, hooki monitora, auto-sync),
  repo dodane do monitora na HA (encja `sensor.pm_car_chatgpt_integration`, dashboard „Projekty").
- Brak kodu i brak zmiany OpenSpec. **Pierwsza sesja robocza zaczyna od `openspec/changes/poc-carplay-command/`**
  (patrz „Pierwsza sesja” niżej).

**Aktywne TODO:** `openspec/changes/*/tasks.md` (jeszcze puste — pierwsza sesja tworzy zmianę).

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
