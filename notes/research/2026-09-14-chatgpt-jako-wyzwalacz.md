# Research: czy ChatGPT (głos) może sam wywołać mój link — i jak robili to inni

Pytanie użytkownika (2026-09-14): „gadam z ChatGPT, on wywołuje link wystawiony na HA, tam leci treść
ustaleń, to idzie do sesji Claude, Claude robi swoje i wystawia odpowiedź pod linkiem, ChatGPT ją czyta".
Założenie przyjęte jako pewnik: **rozmowa ma być z ChatGPT**.

## Odpowiedź krótka

Pomysł jest poprawny architektonicznie i **ludzie zbudowali każdy jego kawałek osobno** — ale nie
z trybu głosowego ChatGPT. Kanał „ChatGPT sam pobiera mój URL" istnieje (agent `ChatGPT-User`), jednak
w trybie głosowym jest to **jedyne** wyjście na zewnątrz i jest niewspierane jako mechanizm wykonawczy:
GPT-Live nie obsługuje apps/konektorów, a rozmowy z własnymi GPT (z Actions) spadają do starego
Advanced Voice **bez akcji**. Czyli: „ChatGPT w aucie woła mój webhook" da się co najwyżej *przemycić*
przez wyszukiwarkę, nie da się na tym oprzeć produkcyjnie.

Jest natomiast ścieżka, która spełnia „gadam z ChatGPT i to wykonuje operacje" **dziś, oficjalnie
i z narzędziami**: ChatGPT jako **model** (OpenAI Conversation) wpięty w Assist w Home Assistancie.
Wtedy mówisz po polsku, słucha Cię GPT, GPT ma narzędzia (skrypty HA), a jeden ze skryptów jest mostem
do Claude'a. To jest dokładnie Twój diagram, tylko „ChatGPT" siedzi po stronie HA, a nie w aplikacji
ChatGPT.

## Co dokładnie ustalono o kanale „ChatGPT pobiera URL"

- OpenAI ma trzy agenty: `GPTBot` (trening), `OAI-SearchBot` (indeks), **`ChatGPT-User` — pobranie
  strony, gdy człowiek o to poprosi, oraz przy GPT Actions**; OpenAI pisze wprost, że „robots.txt rules
  may not apply", bo akcję inicjuje użytkownik [S24].
- Administratorzy widzą te pobrania w logach serwera jako `ChatGPT-User` — to pojedyncze strzały, nie
  wzorzec crawlowania [S25][S26]. Czyli **efekt uboczny GET-a na moim endpoincie jest realny**.
- W trybie głosowym: GPT-Live ma wyszukiwanie web i potrafi sięgnąć po świeże dane [S6][S27], ale
  **„Live does not currently support (…) connected apps, or plugins"**, a **„Live is not available
  inside custom GPT conversations, which continue to use Advanced Voice"** [S27]. Rozmowy z własnym GPT
  w trybie głosowym idą „without (…) custom actions" [S28].
- Jedno źródło wtórne twierdzi dodatkowo, że tryb głosowy nie czyta custom instructions ani historii
  [S27], inne mówi, że pamięć działa [S27]. **Sprzeczność w źródłach wtórnych — DO WERYFIKACJI
  eksperymentem**, bo od tego zależy, czy da się w ogóle „zaprogramować" ChatGPT, żeby sam wołał
  ustalony adres bez dyktowania go za każdym razem.

Praktyczne konsekwencje dla PoC, gdyby iść tą drogą:
- tylko GET, bez nagłówków, bez tajnego tokenu w nagłówku — sekret musiałby siedzieć w ścieżce URL;
- adres trzeba **wypowiedzieć** albo liczyć na pamięć modelu; dyktowanie długiego URL-a w aucie odpada,
  więc domena musi być krótka i wymawialna;
- model może URL-a nie pobrać, pobrać z cache, pobrać *inny* (wyszukać zamiast otworzyć) i nie ma
  potwierdzenia wykonania poza tym, co sam powie;
- odpowiedź wraca jako **streszczenie strony przez model**, nie jako wierny tekst.

## Kto co już zrobił (przegląd)

| kto / co | architektura | działa głosem? | uwagi |
|---|---|---|---|
| Wątek HA Community „Using GPT-3 and Shortcuts to talk with HA" (2023-01-22) [S29] | Siri → Skrót → API GPT (JSON z `service` + `entity_id`) → **webhook HA** → akcja | tak, „Hey Siri, Home Assistant, turn…" | **najbliższy Twojemu pomysłowi i najstarszy**; most robi Skrót, nie ChatGPT |
| Homey jako oficjalna aplikacja w ChatGPT (2026-06) [S30] | ChatGPT Apps SDK / MCP → chmura Homey → urządzenia | **nie w trybie głosowym** | dowód, że nawet oficjalna integracja smart home w ChatGPT nie działa w głosie |
| Custom GPT z Actions → webhook HA (wiele poradników) | ChatGPT (tekst) → Action (OpenAPI) → HA | nie | w głosie Actions są wyłączone [S28] |
| HA MCP Server + Claude / ChatGPT [S31] | klient AI → MCP → encje HA | tekst | to jest most „AI → dom", nie „głos w aucie → dom" |
| `ha-claude`, `claude-homeassistant` (dodatki HA) [S32] | Claude Code **w** HA, pisze automatyzacje | nie | pokazuje, że Claude po stronie HA jest już robiony |
| Omnara, Happy (open source), clauder [S33] | telefon → tunel → Claude Code na serwerze, **tryb głosowy, powiadomienia, zatwierdzenia jednym tapnięciem** | tak, ale w ich aplikacji | **gotowa druga połowa Twojego pomysłu**: „gadanie" do Claude'a z telefonu w drodze |
| Claude Code headless (`claude -p`) wołany z webhooka [S34] | HTTP → serwer → `claude -p` → stdout → odpowiedź | — | to jest dokładnie „wyślij treść do sesji Claude i oddaj wynik" |

Czego **nie** znalazłem mimo celowego szukania: ani jednego opisu działającego układu, w którym
**aplikacja ChatGPT w trybie głosowym** (czy w CarPlay) uruchamia czyjś webhook. To nie znaczy, że nikt
nie próbował — znaczy, że nikt tego nie opublikował jako działającego.

## Dwie wersje Twojego pomysłu

**Wersja A — dosłowna (ChatGPT w aucie woła URL).** Ryzykowna, ale tania do sprawdzenia: jeden publiczny
endpoint z krótkim adresem, wypowiadasz „otwórz <adres> z poleceniem X", sprawdzasz w logu, czy przyszedł
`ChatGPT-User`. Test zajmuje pół godziny i **rozstrzyga sprawę raz na zawsze**, zamiast spekulować.
Nawet jeśli zadziała, nie ma potwierdzenia wykonania ani uwierzytelnienia poza sekretem w ścieżce, więc
nadaje się na zabawkę, nie na zdalne odpalanie Claude'a na moim komputerze.

**Wersja B — ta sama architektura, ChatGPT jako model w HA (rekomendowana).**

```
kierowca (polski) ──▶ Assist w HA  [agent: OpenAI Conversation = ChatGPT]
                          │  narzędzia = skrypty HA
                          ├── scena / urządzenia                (natychmiast)
                          └── script.claude_task ──▶ rest_command ──▶ Command Center
                                                                         │ claude -p
                                                                         ▼
                                                              wynik jako tekst / link
                          ◀── odpowiedź czytana głosem ─────────────────┘
```

- „Gadam z ChatGPT" — spełnione: rozmawiasz z modelem OpenAI, po polsku, głosem.
- Narzędzia działają oficjalnie: skrypty HA są wystawiane agentowi LLM **jako tools**, nie jako encje [S35].
- Most do Claude'a to zwykły `rest_command` z HA do własnego endpointu; endpoint woła `claude -p`
  i zwraca tekst [S34]. Jeśli zadanie jest długie, endpoint zwraca od razu „przyjąłem, wynik pod
  <krótki link>", a wynik dociera powiadomieniem HA na telefon — czyli Twoje „wystawi odpowiedź pod
  linkiem", tylko bez zależności od tego, czy ChatGPT zechce ten link otworzyć.
- Uruchomienie hands-free: „Hey Siri, Home" → Skrót → Assist (jak w zmianie `poc-carplay-command`).
  W CarPlay bez Siri — dotknięcie Assist w aplikacji HA.

Ograniczenie wersji B, uczciwie: to **nie jest** aplikacja ChatGPT i nie ma jej osobowości ani pamięci
konta; to GPT przez API, płatne per token, z kontekstem, który sam zbudujesz w HA.

## Bezpieczeństwo — dwa punkty, które trzeba zaprojektować od razu

1. **Publiczny endpoint uruchamiający Claude Code na moim komputerze** to zdalne wykonanie kodu za
   URL-em. Wymaga: sekretu w ścieżce **plus** whitelisty operacji (PDF mówi o tym wprost: whitelista
   i log), limitu tempa, i tego, żeby Claude działał na katalogu roboczym bez uprawnień do pushowania.
2. **Pośrednie prompt injection**: jeśli wynik pracy Claude'a albo cokolwiek z sieci wraca do modelu,
   treść strony może zawierać instrukcje, które model potraktuje jak polecenie użytkownika — to
   udokumentowana klasa ataków, nie teoria [S36]. Wniosek dla projektu: Command Center przyjmuje
   **polecenia z zamkniętej listy**, nie dowolny tekst do wykonania.

## Rekomendacja (reguła 7.2)

Zostawić dotychczasowy PoC hands-free bez zmian **i dołożyć do niego dwa eksperymenty**, oba tanie:

1. **E1 (pół godziny, rozstrzyga wersję A)**: publiczny endpoint z logiem, próba „otwórz ten adres"
   w ChatGPT — najpierw w tekście, potem głosem, potem głosem w CarPlay. Wynik: czy leci `ChatGPT-User`,
   czy odpowiedź wraca wiernie, ile trwa. Negatyw też jest wynikiem i zamyka temat.
2. **E2 (główna droga)**: pipeline Assist z agentem OpenAI i jednym skryptem-narzędziem `claude_task`,
   który uderza w prosty endpoint z `claude -p`. Zmierzyć tak samo jak resztę PoC.

Dopiero po E1 i E2 wiadomo, czy Command Center ma mieć wejście „URL dla ChatGPT", czy wyłącznie
„narzędzie dla agenta w HA".

## Źródła (odczytane 2026-09-14)

- [S24] OpenAI Developers, „Overview of OpenAI Crawlers”, https://developers.openai.com/api/docs/bots — `ChatGPT-User`: „not used for crawling the web in an automatic fashion… robots.txt rules may not apply”
- [S25] Known Agents, „What Is ChatGPT-User? User Agent & Robots.txt”, https://knownagents.com/agents/chatgpt-user
- [S26] DEV Community, „Your access log already knows whether ChatGPT is citing you”, https://dev.to/shanni/your-access-log-already-knows-whether-chatgpt-is-citing-you-20gp
- [S27] The Rundown AI, „GPT-Live Review: ChatGPT Voice Features, Limits & Price”, https://www.therundown.ai/tools/gpt-live — „Live does not currently support video, screen sharing, connected apps, or plugins”; „Live is not available inside custom GPT conversations”; **sprzeczne zdania o custom instructions/pamięci**
- [S28] Engadget, „How to use ChatGPT's new, more natural Voice Mode for conversations”, https://www.engadget.com/2230975/how-to-use-chatgpt-voice-mode/ — rozmowy z custom GPT „without image generation, data analysis, or custom actions”
- [S29] Home Assistant Community, „Using GPT3 and Shortcuts to talk with Home Assistant in a very smart way”, 2023-01-22, https://community.home-assistant.io/t/using-gpt3-and-shorcuts-to-talk-with-home-assistant-in-a-very-smart-way/522908
- [S30] Basic Tutorials, „Homey now in ChatGPT: Control your smart home by voice”, 2026-06, https://basic-tutorials.com/news/homey-now-in-chatgpt-control-your-smart-home-by-voice/
- [S31] SmartHomeScene, „Home Assistant MCP Server: The Complete Guide”, https://smarthomescene.com/guides/home-assistant-mcp-server-complete-guide/
- [S32] GitHub, `Bobsilvio/ha-claude` (dodatek HA: Claude Code/GPT/Gemini), https://github.com/Bobsilvio/ha-claude ; `philippb/claude-homeassistant`, https://github.com/philippb/claude-homeassistant
- [S33] GitHub, `slopus/happy` (mobilny klient Claude Code z głosem), https://github.com/slopus/happy ; Omnara, https://remote.omnara.com/ ; `ZohaibAhmed/clauder`, https://github.com/ZohaibAhmed/clauder
- [S34] amux, „Claude Code Headless Mode: The Complete Self-Hosting Guide (2026)”, https://amux.io/guides/claude-code-headless/ — `-p` / `--print`, wyzwalanie z webhooka
- [S35] Home Assistant, „Exposing scripts to LLM conversation agents”, https://www.home-assistant.io/voice_control/exposing_scripts_to_llms/ — skrypty stają się **narzędziami** agenta; oraz integracja OpenAI Conversation, https://www.home-assistant.io/integrations/openai_conversation/
- [S36] Unit 42 (Palo Alto Networks), „Fooling AI Agents: Web-Based Indirect Prompt Injection Observed in the Wild”, https://unit42.paloaltonetworks.com/ai-agent-prompt-injection/ ; OWASP Top 10 for Agentic Applications 2026 (ASI01 Agent Goal Hijack)

Źródła [S6] i wcześniejsze — patrz `2026-09-14-mechanizmy-carplay.md`.
