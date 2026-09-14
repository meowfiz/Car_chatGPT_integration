## Why

Cel projektu (PDF, str. 2–3): polecenie głosowe w samochodzie ma uruchamiać operacje na własnej
infrastrukturze i wracać odpowiedzią głosem. PDF zakazuje budowania czegokolwiek, dopóki jeden proof of
concept nie pokaże działającego mostu „głos w aucie → mój endpoint”. Research z 2026-09-14
(`notes/research/2026-09-14-mechanizmy-carplay.md`) rozstrzyga, że **ChatGPT Voice w CarPlay nie ma dziś
żadnego mechanizmu wywołania własnego endpointu** (apps nie działają w trybie głosowym, MCP jest web-only
i nie na planie Go), a jedyny most działający hands-free — Siri i Skróty — **nie mówi po polsku**, więc PoC
musi obejść oba ograniczenia naraz i zmierzyć wynik, zanim zapadnie decyzja o Command Center.

## What Changes

- Jedna rekomendowana ścieżka PoC: **„Hey Siri, Home” w CarPlay → skrót Apple Shortcuts → `Dictate Text`
  z locale `pl_PL` (polecenie po polsku) → App Intent Home Assistant `Assist prompt` (pipeline po polsku)
  → HA wykonuje akcję (scena testowa) → `Speak Text` polskim głosem**. ChatGPT nie jest w pętli;
  opcjonalnie wchodzi jako agent konwersacyjny pipeline'u Assist w HA (integracja OpenAI Conversation),
  nie jako aplikacja ChatGPT.
- **Język**: Siri nie obsługuje polskiego (stan 2026-09-14), więc po angielsku jest wyłącznie dwuwyrazowa
  fraza budząca; polecenie, rozumienie i odpowiedź są po polsku (dyktowanie iOS `pl_PL`, Assist w HA,
  polski głos systemowy). Jakość dyktowania `pl_PL` w hałasie auta jest mierzona osobno jako ryzyko nr 1.
- Scena testowa i pipeline Assist w istniejącym HA (repo `HA`); żadnego nowego serwisu, kontenera ani kodu
  aplikacyjnego.
- Protokół pomiaru: czas od końca wypowiedzi do wykonania akcji w HA (znacznik logbook vs. stoper), czas do
  początku odpowiedzi głosowej, liczba prób udanych / wszystkich, **oraz osobno liczba prób, w których
  dyktowanie `pl_PL` przepisało polecenie poprawnie**, przy co najmniej 10 próbach i 3 różnych poleceniach,
  w jadącym samochodzie.
- Dwa fallbacki zmierzone tym samym protokołem, jeśli ścieżka główna padnie: (A) skrót z `Activate scene`
  na stałe zamiast dyktowania i Assist (sprawdza samą pętlę bez rozpoznawania mowy); (B) Assist w CarPlay
  przez dotknięcie (HA Companion, iOS 26.4+) — w pełni po polsku, ale bez hands-free.
- **Rozmowa z ChatGPT jako założenie** (decyzja użytkownika 2026-09-14): drugi pipeline Assist z agentem
  OpenAI Conversation, w którym skrypty HA są narzędziami modelu, plus most `script.claude_task` →
  `rest_command` → endpoint uruchamiający `claude -p` i zwracający tekst albo link z wynikiem.
- **Eksperyment E1**: sprawdzenie, czy aplikacja ChatGPT potrafi sama pobrać mój publiczny URL (agent
  `ChatGPT-User`) w tekście, głosem i głosem w CarPlay. Rozstrzyga, czy Command Center ma mieć wejście
  „URL dla ChatGPT”. Research wskazuje, że w trybie głosowym to niewspierane, więc E1 ma równie dużą
  wartość jako negatyw.
- Wynik PoC (także negatywny, reguła 5.8) zapisany w `notes/HANDOFF_poc_carplay.md` i decyzja: budować
  Command Center czy nie, i na jakim moście.

## Capabilities

### New Capabilities
- `voice-command-ha-poc`: polecenie głosowe hands-free w CarPlay uruchamia akcję w Home Assistant i wraca
  odpowiedzią głosową; kapabilność definiuje przepływ, warunki zaliczenia próby i protokół pomiaru.

### Modified Capabilities
<!-- brak — openspec/specs/ jest pusty -->

## Impact

- **Home Assistant** (repo `D:\claude_projects\HA`): nowa scena `scene.poc_carplay_test` (lub równoważna),
  nowy lub istniejący pipeline Assist z TTS; opcjonalnie integracja OpenAI Conversation jako agent. Zmiany
  konfiguracyjne, odwracalne.
- **iPhone**: aplikacja HA Companion (App Intents), aplikacja Skróty, jeden skrót o angielskiej nazwie.
  Wymaga Siri ustawionej na język obsługiwany (polskiego nie ma), włączonego „Hey Siri” w CarPlay,
  polskiej klawiatury z dyktowaniem i uprawnienia skrótu do działania bez pytania.
- **To repo**: brak kodu; tylko `notes/` i `openspec/`. Kod pojawi się dopiero po decyzji z PoC.
- **Poza zakresem**: Command Center, MCP, GitHub, Claude Code, własna aplikacja iOS, zmiana planu ChatGPT.
