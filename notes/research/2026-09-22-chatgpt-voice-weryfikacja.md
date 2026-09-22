# Weryfikacja PDF-u „Voice + CarPlay + Claude + własne repozytorium" (2026-09-22)

Wejście: `podsumowanie_voice_claude_carplay.pdf` w korzeniu repo — podsumowanie rozmowy z ChatGPT
z 22.09.2026, które kończy się rekomendacją „weź wzorzec z `talk-to-claude-code`".
Pytanie użytkownika: **czy jednak da się użyć interfejsu głosowego Voice od ChatGPT.**

Prowenienecja: wszystkie cztery źródła z PDF-u sprawdzone tego samego dnia przez pobranie strony
GitHuba albo wyszukiwarkę; stan ChatGPT Voice potwierdzony dwoma niezależnymi źródłami
(pomoc OpenAI + wątek deweloperski).

## Odpowiedź krótka

**Nie — i PDF, wbrew tytułowi, też tego nie proponuje.** Projekt, który PDF wskazuje jako wzorzec,
działa na **Grok Voice**, nie na ChatGPT Voice, właśnie dlatego, że Grok umie w trybie głosowym
sięgnąć po własny konektor MCP, a ChatGPT nadal nie umie. Ustalenie z sesji 1 (2026-09-14) trzyma
się bez zmian; zmieniło się tylko to, że ChatGPT jest od marca 2026 natywnie w CarPlay — jako
usta i uszy bez rąk.

## Weryfikacja źródeł z PDF-u

| źródło z PDF | stan zmierzony 2026-09-22 | konsekwencja |
|---|---|---|
| `osaighi/talk-to-claude-code` | **istnieje**; README: „built to work from a car: **Grok's voice mode** on CarPlay"; MCP → wstrzyknięcie promptu do kolejki żywej sesji Claude Code przez gniazda uniksowe (bez patchowania binarki i bez przechwytywania TLS); 31 commitów; wymaga Node 22+ i Claude Code ≥ 2.1.229 | to **dowód przeciw** ChatGPT Voice, a nie za nim: autor wybrał innego klienta głosowego |
| `fireishott/Herald` | istnieje, ale **zarchiwizowany 2026-08-06** (read-only); natywny klient iOS (Swift 6.2, iOS 18+) do frameworka Hermes Agent, własne STT/TTS (MiMo), CarPlay, MCP, Tailscale albo własny relay | to **własna aplikacja iOS**, nie ChatGPT Voice — najdroższa ścieżka, i porzucona przez autora |
| `anthropics/claude-ai-mcp` — „zgłoszenie dot. MCP w Voice" | repo istnieje (547 otwartych zgłoszeń), ale **zgłoszenia o Voice nie potwierdziłem** — widoczne dotyczą OAuth i konektorów. **DO WERYFIKACJI** | teza („Claude Voice + MCP też nie jest pewne") prawdopodobnie prawdziwa, ale **cytat w PDF-ie podany pod zły adres** |
| `Gillinghammer/realtime-to-mcp` | niesprawdzone, bo nieistotne dla pytania: Realtime API to **własny klient głosowy**, nie aplikacja ChatGPT | nie jest ścieżką „ChatGPT Voice" |

Wniosek o PDF-ie: jego rekomendacja jest sensowna technicznie, ale **milczy o cenie** — kupuje
hands-free w aucie pod warunkiem zmiany klienta głosowego z ChatGPT na Grok-a.

## Stan ChatGPT Voice na 2026-09-22

- **CarPlay: jest.** OpenAI udostępniło ChatGPT w CarPlay w marcu 2026 (wymaga iOS 26.4+), na
  wszystkich planach bez dopłaty. Głos jest podstawowym trybem. Lipiec 2026 dołożył barge-in
  (można modelowi wejść w słowo).
- **Ale bez rąk i bez słowa budzącego:** nie ma wake worda (trzeba otworzyć aplikację) i ChatGPT
  **nie może sterować funkcjami telefonu ani auta**.
- **Tryb głosowy nadal nie obsługuje apps/konektorów/własnych MCP.** Potwierdzone niezależnie:
  pomoc OpenAI („voice mode currently does not support apps"; własne zdalne serwery MCP niedostępne
  w interfejsie głosowym) oraz otwarty wątek na OpenAI Developer Community — „text sessions works
  fine, but fails as soon as switched to voice", bez odpowiedzi OpenAI i bez terminu.
- Dla porównania: Grok dorzucił „Bring Your Own MCP" w połowie 2026 na planach płatnych, a Voice
  Agent Builder (beta, 1.07.2026) ma natywne MCP. **To jest cała różnica między tymi dwoma
  klientami** i cała przyczyna wyboru autora `talk-to-claude-code`.

## Trzy sposoby „jednak użyć ChatGPT Voice", od najtańszego

**C — „Ask ChatGPT" jako akcja w Skrócie (wybrane do realizacji, OpenSpec 3.7–3.9).**
Siri → Skrót → `Dictate Text` (`pl_PL`) → POST do mostu `?style=facts` → akcja **Ask ChatGPT**
(oficjalna, z aplikacji ChatGPT) → `Speak Text`. Głosem odzywa się ChatGPT, ale **ręce ma Skrót**,
nie model. Koszt: jedna akcja więcej w skrócie z grupy 3 plus jeden parametr w moście.
Ograniczenie, uczciwie: uruchamiane Siri, a nie ciągła rozmowa, i **dokłada jeden przelot modelu
do pętli, która i tak nie trafia w próg 15 s** — dlatego wariant ma własną prerejestrację
z warunkiem negatywu, a nie zgodę z góry.

**A — dosłowna: ChatGPT sam woła mój URL.** Bez zmian od 14.09: kanał `ChatGPT-User`, GET bez
nagłówków, sekret w ścieżce, odpowiedź jako streszczenie modelu, zero potwierdzenia wykonania.
To wciąż **eksperyment E1** (zadania 6.1–6.2), wciąż nierobiony; pół godziny i zamyka temat.
Fakt, że ChatGPT jest teraz w CarPlay, robi z E1 test tańszy, nie mniej potrzebny.

**B — ChatGPT jako model w Assist (OpenAI Conversation).** Bez zmian: pełne narzędzia, polski
głos, ale to GPT przez API, nie aplikacja ChatGPT, i płatne per token.

Czego na liście **nie ma**: „ChatGPT Voice → MCP → Claude". Tego dziś nie da się zbudować.

## Co z tego wzięliśmy do `talk-to-claude-code`

**Nie architekturę, tylko jeden mechanizm:** wstrzykiwanie promptu do **żywej** sesji Claude Code
zamiast startu `claude -p` od zera. To adresuje zadanie 2.7 — zmierzona mediana `claude -p` to
**14,1 s** (sesja 3), czyli koszt startu, nie głosu. Front MCP z tego projektu ma sens wyłącznie
przy zgodzie na Grok Voice zamiast ChatGPT; to decyzja użytkownika, nie techniczna.

## Ryzyko dołożone przez wariant C

Treść z repozytoriów trafia do modelu OpenAI (pośrednie prompt injection — klasa ataków opisana
w `2026-09-14-chatgpt-jako-wyzwalacz.md`). Tutaj skutek jest ograniczony: ChatGPT w Skrócie
**tylko mówi**, nie ma narzędzi, więc najgorsze, co może zrobić, to przeczytać kierowcy cudze
zdanie. Drugie ryzyko jest prywatnościowe i realne: fragmenty notatek i stanu repozytoriów wychodzą
poza tailnet. Wariant główny (Whisper + most) tego nie robi i pozostaje ścieżką domyślną.

## Źródła (odczytane 2026-09-22)

- GitHub, `osaighi/talk-to-claude-code` — https://github.com/osaighi/talk-to-claude-code
- GitHub, `fireishott/Herald` (archived 2026-08-06) — https://github.com/fireishott/Herald
- OpenAI Help Center, „Using ChatGPT in CarPlay" — https://help.openai.com/en/articles/20001153-using-chatgpt-in-carplay
- OpenAI Help Center, „Apps in ChatGPT" — https://help.openai.com/en/articles/11487775-connectors-in-chatgpt
- OpenAI Developer Community, „ChatGPT Support of MCP in Voice Mode on Web and Android" — https://community.openai.com/t/chatgpt-support-of-mcp-in-voice-mode-on-web-and-android/1382072
- 9to5Mac, „ChatGPT app launches for CarPlay on iOS 26.4" (2026-03-31) — https://9to5mac.com/2026/03/31/chatgpt-app-launches-for-carplay-on-ios-26-4/
- 9to5Mac, „OpenAI just upgraded ChatGPT voice mode… including CarPlay" (2026-07-08) — https://9to5mac.com/2026/07/08/openai-upgrading-chatgpt-with-all-new-voice-mode-experience-watch-here/
- xAI Docs, „Connectors" — https://docs.x.ai/grok/connectors
- `anthropics/claude-ai-mcp` — https://github.com/anthropics/claude-ai-mcp (zgłoszenie o Voice **DO WERYFIKACJI**)
