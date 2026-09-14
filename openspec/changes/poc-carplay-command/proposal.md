## Why

Cel projektu (PDF, str. 2–3): polecenie głosowe w samochodzie ma uruchamiać operacje na własnej
infrastrukturze i wracać odpowiedzią głosem. Doprecyzowanie użytkownika z 2026-09-14: chodzi przede
wszystkim o **rozmowę z project_monitorem** — „jakbym gadał w oknie Claude Code do project monitora",
z dostępem do wszystkich repozytoriów łącznie z HA, i o odpowiedź na dowolne pytanie.

Research z tego samego dnia (`notes/research/2026-09-14-*.md`) ustalił trzy rzeczy, które wyznaczają
kształt PoC:

- **Aplikacja ChatGPT w trybie głosowym nie zadzwoni do żadnego endpointu** — apps i MCP są tam
  wyłączone, a własne GPT z Actions spadają do trybu bez akcji. ChatGPT nie może być mostem.
- **Subskrypcja Go nie podłącza się do Home Assistanta.** Integracja OpenAI w HA używa osobno płatnej
  platformy API; abonament ChatGPT nie obejmuje wywołań API. Nie ma czego podpiąć.
- **Siri nie mówi po polsku** i nie będzie warstwą rozpoznawania mowy. To, co w ChatGPT brzmi jak
  „perfekcyjne zbieranie głosu po polsku", to rodzina modeli Whisper — i **ten sam model można wywołać
  samemu**, z poziomu skrótu iOS. Tak robią to inni: skrót nagrywa dźwięk i wysyła go do transkrypcji,
  zamiast liczyć na dyktowanie systemowe.

## What Changes

- PoC celuje w **pytanie o projekt, nie w scenę**: „co się dzieje z projektem X" → odpowiedź głosem po
  polsku. Scena w HA zostaje wyłącznie jako najprostszy test samej pętli, bo zostawia twardy ślad
  w dzienniku zdarzeń.
- Łańcuch rekomendowany: **„Hey Siri, Monitor" → skrót → `Record Audio` o stałej długości → POST dźwięku
  do project_monitora → transkrypcja Whisper (najpierw lokalnie na komputerze w tailnecie) → Claude
  z dostępem do repozytoriów → tekst odpowiedzi → `Speak Text` polskim głosem**. Siri słyszy wyłącznie
  dwa angielskie słowa; całe polskie zdanie idzie do Whispera.
- **Claude jest mózgiem**, nie OpenAI. Użytkownik ma go opłaconego i ma on dostęp do repozytoriów.
  Do HA nie wchodzi żaden agent chmurowy, więc zasada „w pełni offline" z repo `HA` zostaje nienaruszona.
- Nowe wejście w project_monitorze: endpoint przyjmujący nagranie albo tekst pytania i zwracający
  odpowiedź (`claude -p` z dostępem tylko do odczytu), z sekretem, limitem tempa i logiem.
- Dwa warianty zapasowe mierzone tym samym protokołem: (A) `Dictate Text` z locale `pl_PL` zamiast
  nagrania, jeśli `Record Audio` uruchamiane przez Siri okaże się zawodne; (B) start przez dotknięcie
  Assist w aplikacji HA w CarPlay, bez Siri.
- Eksperyment E1 („czy ChatGPT sam pobierze mój link") zostaje jako tani test rozstrzygający, ale nie
  jest fundamentem architektury.

## Capabilities

### New Capabilities
- `voice-command-ha-poc`: polecenie i pytanie głosowe hands-free w samochodzie trafia do własnego
  backendu, wraca odpowiedzią głosową po polsku; kapabilność definiuje przepływ, warstwy rozpoznawania
  mowy, warunki zaliczenia próby i protokół pomiaru.

### Modified Capabilities
<!-- brak — openspec/specs/ jest pusty -->

## Impact

- **project_monitor** (repo `project_integration`, dodatek HA z FastAPI): nowy endpoint pytań obok
  istniejących `/api/state`, `/api/repo/{name}/tasks`, `/api/repo/{name}/events`. Autoryzacja tokenem
  już tam jest.
- **Komputer w tailnecie**: lokalna transkrypcja (faster-whisper) i `claude -p` z dostępem do repozytoriów
  w trybie tylko do odczytu.
- **Home Assistant** (repo `HA`): scena testowa plus alias głosowy przez `voice/voice_data.yaml`
  i generator; **bez agenta chmurowego**, bez zmiany potoku offline.
- **iPhone**: skrót iOS, włączona Siri z językiem angielskim wyłącznie jako wyzwalacz.
- **Poza zakresem**: Command Center jako utrzymywany serwis, MCP, integracje GitHub i Claude Code poza
  jednym wywołaniem, własna aplikacja CarPlay, zmiana planu ChatGPT.
