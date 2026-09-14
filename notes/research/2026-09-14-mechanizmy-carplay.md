# Research: jak głos w CarPlay na iPhonie może wywołać własny endpoint (stan na 2026-09-14)

Pytanie z PDF (str. 3): „jak ChatGPT z CarPlay ma wywołać ten endpoint”. Pięć ścieżek kandydujących,
każda sprawdzona pod trzema kątami: **działa w samochodzie bez dotykania telefonu?**, **wymaga planu
wyżej niż Go?**, **wymaga własnej aplikacji iOS?**. Źródła z datami na końcu; twierdzenia bez źródła
oznaczone „DO WERYFIKACJI” (reguła 6.3).

## Język polski — ograniczenie, które zmienia kształt ścieżki 2

**Siri nie obsługuje języka polskiego** (stan 2026-09-14): polskiego nie ma ani na liście języków Siri,
ani Apple Intelligence; WWDC 2025 dołożyło osiem języków i polskiego wśród nich nie było [S18][S19].
Polska Siri jest zapowiadana „kiedyś" (spekulacje o iOS 27), ale dziś jej nie ma [S20].

Konsekwencje dla PoC:

- **Fraza budząca musi być w języku Siri** (np. angielskim): „Hey Siri, Home". To dwa słowa; reszta może
  być po polsku.
- **Polecenie nie może iść przez `Ask for Input` Siri** — Siri zapyta i będzie słuchać po angielsku.
  Zamiast tego w skrócie używamy akcji **`Dictate Text` z wymuszonym językiem `pl_PL`**: dyktowanie iOS
  (to samo, co mikrofon na klawiaturze) obsługuje polski niezależnie od języka Siri, a akcja przyjmuje
  kod locale jako parametr wejściowy [S21][S22].
- **Odpowiedź czytana po polsku**: akcja `Speak Text` z głosem polskim (np. „Zosia"); iOS ma polskie
  głosy systemowe niezależnie od Siri [S23].
- **Rozumienie polecenia po polsku robi Home Assistant**, nie Apple: pipeline Assist z polskim agentem
  (wbudowany HA ma polskie intencje; agent LLM rozumie polski swobodnie).

Czyli po polsku jest **całe polecenie i cała odpowiedź**; po angielsku tylko dwuwyrazowe „Hey Siri, Home".
To jest cena tej ścieżki i trzeba ją zmierzyć osobno: jakość dyktowania `pl_PL` w hałasie auta jest
ryzykiem numer 1 (nie Siri, tylko dyktowanie).

Alternatywy w pełni polskie, bez ani jednego angielskiego słowa:
- **Ścieżka 3** (Assist w CarPlay przez dotknięcie): STT po stronie HA (Whisper/cloud), polski od początku
  do końca — ale wymaga dotknięcia ekranu, więc nie jest hands-free.
- **ChatGPT Voice w CarPlay** mówi po polsku bardzo dobrze — i nadal nie umie wywołać niczego (ścieżka 1).

## Wynik w jednym zdaniu

**ChatGPT Voice (także w CarPlay) nie ma dziś żadnego mechanizmu wywołania zewnętrznego endpointu
na żadnym planie konsumenckim** — apps/MCP nie działają w trybie głosowym ani na mobile, a Developer
mode jest web-only i nie obejmuje Go. Jedyna ścieżka działająca hands-free dziś, bez własnej aplikacji
i bez zmiany planu, to **Siri → Apple Shortcuts → Home Assistant (App Intents / webhook) → odpowiedź
głosem przez Siri**. ChatGPT może w tej ścieżce być „mózgiem” tylko pośrednio: jako model
konwersacyjny Assist w HA (integracja OpenAI Conversation) albo przez akcję Skrótów „Use Model”.

## Ścieżki

### 1. ChatGPT Voice w CarPlay → apps / konektory / MCP → mój endpoint — NIE DZIAŁA

| kryterium | stan |
|---|---|
| hands-free w aucie | tak, ale bez wake worda (trzeba raz dotknąć ikonę w CarPlay) [S3][S7] |
| plan Go wystarcza | do samej rozmowy tak (CarPlay na wszystkich planach) [S1]; do wywołania endpointu — nie ma czego kupić |
| własna aplikacja | nie |

Fakty:
- OpenAI Help „Apps in ChatGPT” (aktualizacja ok. 2026-09-11): **„Voice mode currently does not
  support apps.”** [S2]
- OpenAI Help „Developer mode and MCP apps” (aktualizacja ok. 2026-08-21): pełne MCP z akcjami zapisu
  w becie dla **Business, Enterprise, Edu**; FAQ: **„Are MCP apps available on mobile? No - web only.”** [S4]
- developers.openai.com, guide Developer mode: dostępny dla **Pro, Plus, Business, Enterprise, Education
  „on the web”** — Go i Free poza listą [S5]
- OpenAI Help „Using ChatGPT in CarPlay” (aktualizacja ok. 2026-08-29): iOS 26.4+, „available globally
  on all ChatGPT plans”, „cannot control your car or affect other apps” [S1]
- Kategoria Apple „voice-based conversational apps” (iOS 26.4, ChatGPT od 2026-04-02): tylko głos,
  brak wake worda, start przez dotknięcie ikony, izolacja od Map/Muzyki/danych auta [S3][S7][S8]
- Nowy tryb głosowy GPT-Live (2026-07-08) ma web search, ale bez apps/konektorów; od 2026-09-09 Go ma
  3 h GPT-Live-1 mini [S6][S9]

Wniosek: ślepa uliczka **dziś**, niezależnie od planu. Wraca do gry dopiero, gdy OpenAI doda apps do
trybu głosowego na mobile (obserwować changelog).

### 2. Siri → Apple Shortcuts → Home Assistant → odpowiedź głosem — DZIAŁA, REKOMENDOWANA

| kryterium | stan |
|---|---|
| hands-free w aucie | **tak**: „Hey Siri, <nazwa skrótu>” działa w CarPlay [S10][S11]; nazwa musi być w języku Siri (polskiego Siri nie ma — patrz sekcja o języku) |
| plan Go wystarcza | tak — ChatGPT w ogóle nie jest w pętli (opcjonalnie jako model w HA) |
| własna aplikacja | nie — aplikacja HA Companion daje App Intents [S12] |

Fakty:
- HA Companion App Intents (Skróty): **Assist prompt** (tekst → pipeline Assist → odpowiedź jako dane),
  **Perform action**, **Activate scene**, **Run script**, **Trigger automation**, **Render template**;
  „You can launch any of your created Shortcuts using Siri from an iPhone…” [S12]
- Wątek HA Community (2025-06-28…10): wariant bez App Intents — REST `conversation/process` + Piper TTS
  w skrócie; problemy z odtwarzaniem audio na HomePodach, brak pomiarów, brak testu w CarPlay [S13]
- iOS 26: akcja Skrótów **„Use Model”** z ChatGPT jako modelem (tylko iPhone z Apple Intelligence) —
  możliwe parsowanie intencji w skrócie; **DO WERYFIKACJI** czy działa z Siri w CarPlay [S14]
- Polecenie po polsku wchodzi przez `Dictate Text` z locale `pl_PL`, nie przez `Ask for Input` Siri
  (sekcja o języku wyżej) — **DO WERYFIKACJI w aucie**, czy dyktowanie startuje i kończy się samo bez
  dotknięcia ekranu; to jest ryzyko nr 1 PoC

Ograniczenia: fraza budząca po angielsku; Siri nie prowadzi rozmowy wieloturowej jak ChatGPT Voice;
każde polecenie = jedno wywołanie skrótu.

### 3. Home Assistant Assist w CarPlay (aplikacja HA Companion) — DZIAŁA, ALE PRZEZ DOTYK

| kryterium | stan |
|---|---|
| hands-free w aucie | **nie**: start przez dotknięcie „Assist” w Quick Access; brak Siri i wake worda [S15] |
| plan Go wystarcza | tak (ChatGPT poza pętlą) |
| własna aplikacja | nie |

Wymaga iOS 26.4+ i HA Companion 26.4+; odpowiedź TTS przez audio auta; „Assist prompts” jako gotowe
przyciski [S15]. Dobry **fallback** dla PoC, gdyby Siri + skrót nie chciały słuchać w aucie; miernik
porównawczy latencji pipeline’u.

### 4. Własna aplikacja iOS z entitlementem CarPlay „voice-based conversation” — MOŻLIWA, NIE TERAZ

Entitlement `com.apple.developer.carplay-voice-based-conversation` od iOS 26.4, każdy wniosek
recenzuje Apple; aplikacja tylko głosowa, bez wake worda, start dotknięciem, izolacja od systemu [S3][S8].
Backend własny może robić co chce (to tylko sieć), ale koszt: konto deweloperskie, Swift, recenzja
entitlementu (tygodnie), a i tak start przez dotknięcie. Non-goal do czasu, gdy PoC ze ścieżki 2 pokaże,
że sama Siri jest zbyt ograniczona.

### 5. Siri → rozszerzenie ChatGPT („zapytaj ChatGPT”) — NIE DAJE ENDPOINTU

Siri z Apple Intelligence przekazuje pytanie do ChatGPT, ale odpowiedź wraca jako tekst/mowa; ChatGPT
w tej roli nie ma narzędzi ani apps [S16]. iOS 27 ma otworzyć „Extensions” dla Gemini/Claude (raport
2026-05-05) — nadal odpowiedź, nie akcja [S17].

## Rekomendacja (reguła 7.2)

PoC = ścieżka **2**: skrót o angielskiej nazwie („Hey Siri, Home") w CarPlay → `Dictate Text` z locale
`pl_PL` (polecenie po polsku) → App Intent HA **Assist prompt** (pipeline Assist po polsku) → HA wykonuje
akcję (scena) → treść odpowiedzi → **Speak Text** polskim głosem. Zero kodu, wszystko już zainstalowane,
mierzalne w jednej sesji w aucie. Fallback A: zamiast Assist prompt — „Activate scene" na stałe (test, czy
sama pętla Siri → HA → mowa działa, bez dyktowania). Fallback B: ścieżka 3 (dotyk, w pełni po polsku) do
porównania latencji i jakości rozpoznania.

Co PoC **nie** rozstrzyga: czy kiedykolwiek ChatGPT Voice będzie mógł wołać endpoint; to zależy od OpenAI.

## Źródła

- [S1] OpenAI Help Center, „Using ChatGPT in CarPlay”, https://help.openai.com/en/articles/20001153-using-chatgpt-in-carplay — „Updated 16 days ago” odczytane 2026-09-14 (≈2026-08-29)
- [S2] OpenAI Help Center, „Apps in ChatGPT”, https://help.openai.com/en/articles/11487775-connectors-in-chatgpt — „Updated 3 days ago” odczytane 2026-09-14 (≈2026-09-11); cytat „Voice mode currently does not support apps.”
- [S3] MacRumors, „OpenAI Brings ChatGPT to CarPlay for Hands-Free Voice Conversations”, 2026-03-31, https://www.macrumors.com/2026/03/31/openai-chatgpt-carplay/
- [S4] OpenAI Help Center, „Developer mode and MCP apps in ChatGPT”, https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt — „Updated 24 days ago” odczytane 2026-09-14 (≈2026-08-21)
- [S5] OpenAI Developers, „ChatGPT Developer mode”, https://developers.openai.com/api/docs/guides/developer-mode — odczytane 2026-09-14, bez daty publikacji
- [S6] 9to5Mac, „OpenAI just upgraded ChatGPT voice mode in a major way, including CarPlay”, 2026-07-08, https://9to5mac.com/2026/07/08/openai-upgrading-chatgpt-with-all-new-voice-mode-experience-watch-here/
- [S7] mayhemcode, „Apple CarPlay AI Apps Explained: Rules, Limits, and What Comes Next”, 2026-04-09, https://www.mayhemcode.com/2026/04/apple-carplay-ai-apps-explained-rules.html
- [S8] AppleInsider, „AI agents are coming to CarPlay, but they're not getting the keys”, 2026-02-18, https://appleinsider.com/articles/26/02/18/ai-agents-are-coming-to-carplay-but-theyre-not-getting-the-keys ; Apple Developer, „Requesting CarPlay Entitlements”, https://developer.apple.com/documentation/carplay/requesting-carplay-entitlements
- [S9] Releasebot, „ChatGPT Updates by OpenAI — September 2026”, wpisy 2026-08-25 i 2026-09-09, https://releasebot.io/updates/openai/chatgpt (agregator; DO WERYFIKACJI wobec oficjalnych release notes)
- [S10] Apple Support, „Use Siri in your car on iPhone”, https://support.apple.com/guide/iphone/use-siri-in-your-car-iph0aa8c80e6/ios — odczytane 2026-09-14
- [S11] Apple Support, Shortcuts User Guide, „Run shortcuts with Siri”, https://support.apple.com/en-ie/guide/shortcuts/apd07c25bb38/ios — odczytane 2026-09-14
- [S12] Home Assistant Companion Docs, „Apple App Intents”, https://companion.home-assistant.io/docs/integrations/siri-shortcuts/ — odczytane 2026-09-14
- [S13] Home Assistant Community, „Talk to your HA Voice Assistant via Siri”, wątek od 2025-06-28, https://community.home-assistant.io/t/talk-to-your-ha-voice-assistant-via-siri/905997
- [S14] AppleInsider, „How to use Siri with ChatGPT on older iPhones without Apple Intelligence” (opis akcji „Use Model” w iOS 26), https://appleinsider.com/inside/ios/tips/how-to-use-siri-with-chatgpt-on-older-iphones-without-apple-intelligence — odczytane 2026-09-14
- [S15] Home Assistant Companion Docs, „CarPlay → Assist”, https://companion.home-assistant.io/docs/carplay/assist/ — odczytane 2026-09-14 (wymaga iOS 26.4+, app 26.4+)
- [S16] Apple Support, „Use ChatGPT with Apple Intelligence on iPhone”, https://support.apple.com/guide/iphone/use-chatgpt-with-apple-intelligence-iph00fd3c8c2/ios — odczytane 2026-09-14
- [S17] 9to5Mac, „iOS 27 will let you choose between Gemini, Claude, and more for AI features: report”, 2026-05-05, https://9to5mac.com/2026/05/05/ios-27-will-let-you-choose-between-gemini-claude-and-more-for-ai-features-report/

- [S18] Apple Community, „When will support for the Polish language be added to Siri and Apple Intelligence?”, https://discussions.apple.com/thread/256082630 — odczytane 2026-09-14 (wątek użytkowników; potwierdza brak polskiego)
- [S19] MacRumors, „iOS 26.1 Adds New Apple Intelligence Languages…”, 2025-09-22, https://www.macrumors.com/2025/09/22/ios-26-1-apple-intelligence-languages/ — lista języków bez polskiego
- [S20] ThinkApple, „Będzie Siri po polsku! Mamy to czarno na białym (aktualizacja)”, 2026-06-08, https://thinkapple.pl/2026/06/08/polska-siri-pl-po-polsku-kiedy/ — zapowiedzi, brak daty wdrożenia; **DO WERYFIKACJI** wobec oficjalnego Apple
- [S21] MacStories, „How to Dictate iMessages in Multiple Languages from a Widget with Shortcuts”, https://www.macstories.net/ios/how-to-dictate-imessages-in-multiple-languages-from-a-widget-with-shortcuts/ — kod locale (`pl_PL`) jako wejście akcji `Dictate Text`; odczytane 2026-09-14; **DO WERYFIKACJI na iOS 26**
- [S22] Apple Support, „Dictate text on iPhone”, https://support.apple.com/guide/iphone/dictate-text-iph2c0651d2/ios — dyktowanie zależne od języka klawiatury, nie od Siri; odczytane 2026-09-14
- [S23] Apple Community, „How to set the correct language of Text-To-Speech (Speak Text)”, https://discussions.apple.com/thread/253839272 — wybór głosu/języka w akcji `Speak Text`; polski głos „Zosia”; odczytane 2026-09-14

Uwaga metodyczna: strony help.openai.com blokują pobieranie bez JavaScriptu (HTTP 403); treść [S1][S2][S4]
odczytana przez proxy tekstowe r.jina.ai — cytaty warto potwierdzić w przeglądarce przed cytowaniem dalej.
