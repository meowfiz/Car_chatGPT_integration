# Front glosowy w aucie: ciagla rozmowa przez Grok Voice + MCP

## Why

**Decyzja uzytkownika 2026-09-22: „rozmowa najwazniejsza".** Dotychczasowy PoC celowal w jeden
strzal — pytanie, odpowiedz, koniec. To byl swiadomy wybor pod Siri i Whispera. Cel sie zmienil:
w aucie ma byc **rozmowa wieloturowa** z wlasnymi repozytoriami po drugiej stronie.

Trzy ustalenia zmierzone 2026-09-22 (`notes/research/2026-09-22-chatgpt-voice-weryfikacja.md`)
przesadzaja o ksztalcie tej zmiany:

1. **ChatGPT Voice nie zamknie tej petli i nie zapowiada, ze zamknie.** Tryb glosowy nie obsluguje
   apps, konektorow ani wlasnego MCP — potwierdzone pomoca OpenAI i otwartym watkiem
   deweloperskim bez odpowiedzi. ChatGPT jest w CarPlay od marca 2026, ale jako usta i uszy bez rak.
2. **Grok Voice te petle zamyka dzis.** Jest w CarPlay od maja 2026, a jego tryb glosowy **siega po
   wlasne konektory MCP**. `osaighi/talk-to-claude-code` zbudowano wokol niego wprost z tego powodu,
   z drugim, rownie waznym: Grok **odpytuje w petli** (`get_reply`), zamiast poddac sie po pierwszym
   timeoucie — bez tego dluzsze zadanie Claude'a nie ma jak wrocic glosem.
3. **Mozg juz istnieje i nie wolno go budowac drugi raz.** `monitor/ask_core.py` jest juz unia
   tego, co ten projekt i `project_integration` zbudowaly osobno; `tools/voice_gateway.py`
   (STT/TTS lokalnie, routing do orchestratora) i `monitor/execute_worker.py` (zlecenia z bramkami,
   galaz, PR) dzialaja. Ta zmiana **nie dodaje mozgu** — dodaje przed nim jeden front.

## What changes

1. **Serwer MCP `poc/grok_mcp.py` jako cienka warstwa przed orchestratorem.** Wystawia narzedzia
   dla klienta glosowego i **nie zawiera zadnego rozumowania**: kazde pytanie idzie do
   `POST /api/agent/chat` orchestratora, kazde zlecenie do istniejacej sciezki wykonawczej.
   Zero nowego promptu, zero drugiego `claude -p`, zero drugiej listy repozytoriow.
2. **Rozmowa ma stan po naszej stronie, nie po stronie klienta.** Narzedzia `ask` (przyjmuje
   wypowiedz, oddaje natychmiast token) i `get_reply` (odpytywane w petli do skutku) na sesji
   nazwanej przez klienta. Powod jest twardy: jedno wywolanie nie zmiesci sie w timeoucie klienta
   glosowego, a zmierzona mediana to 14,1 s przy ogonie do 34,5 s.
3. **Kontekst rozmowy trzyma sesja**, nie pojedyncze pytanie: n ostatnich tur wchodzi do promptu,
   zeby „a co z tym drugim projektem" znaczylo cokolwiek. Limit dlugosci historii jest parametrem
   i ma wlasny pomiar (zadanie 4.3), a nie wartosc z sufitu.
4. **Sciezka zapasowa bez MCP**: `GET/POST /voice/ask` i `/voice/reply` z tokenem w sciezce albo
   w query — te same, ktorych uzywa `talk-to-claude-code`, bo Skroty iOS nie ustawiaja naglowkow.
   Dzieki temu dotychczasowy skrot **nie idzie do kosza**, gdy MCP w glosie zawiedzie.
5. **Wystawienie przez Tailscale Funnel ze stabilna nazwa hosta** (konektor klienta nie znosi
   zmieniajacego sie adresu) — i to jest **jedyna powazna cena tej zmiany**, patrz `design.md`.
6. **`poc/ask_server.py` przechodzi w stan zamkniety**: zostaje jako sciezka zapasowa dla skrotu,
   nie dostaje nowych funkcji; jego rdzen i tak ma zostac zastapiony przez `ask_core`
   (zmiana `ask-core-client`).

## Czego to NIE zmienia i NIE twierdzi

- **Nie zastepuje Remote Control i nie jest jego duplikatem.** `/remote-control` (Claude Code,
  dostepne na Pro/Max/Team/Enterprise) podlacza **zywa lokalna sesje** do claude.ai/code
  i aplikacji mobilnej, z pelnym lokalnym srodowiskiem. Ale: **nie ma API** (klucze API wprost
  niewspierane) i **nie ma CarPlay**, wiec nie da sie go wolac z HA ani z klienta glosowego.
  To jest kanal dla czlowieka z telefonem w reku, nie dla mostu. Oba maja sens obok siebie.
- **Nie obiecuje wejscia do dowolnego otwartego okna.** Spike z 2026-09-17
  (`monitor/live_sessions.py`) ustalil, ze nic w CLI nie wstrzykuje promptu do dzialajacego
  interaktywnego okna; `claude -p --resume <id>` kontynuuje **kontekst** sesji, ale sensownie
  tylko gdy okno jest bezczynne, bo przeciw zajetemu forkuje kopie — dwie sesje w jednym repo,
  czyli dokladnie ryzyko z reguly 2.7. Ta zmiana **respektuje to ograniczenie**: rozmawiamy
  z sesja, ktora nalezy do mostu, a o cudzych oknach mozemy tylko **powiedziec**, co robia.
  (Uwaga: Remote Control czesciowo podwaza wniosek „nie da sie wejsc do zywego okna" — dla sesji
  uruchomionych z `/remote-control` da sie, tyle ze **z aplikacji, nie programowo**. Notatke
  w `live_sessions.py` trzeba zaktualizowac — zadanie 1.4.)
- **Nie przesadza o subskrypcji.** „Bring Your Own MCP" u Grok-a jest na planach platnych; jesli
  uzytkownik tego nie wykupi, zostaje sciezka zapasowa z punktu 4 i jeden strzal zamiast rozmowy.
- **Nie obiecuje startu bez rak.** Apple w iOS 26.4 nie daje aplikacjom glosowym slowa budzacego —
  ChatGPT, Grok i Perplexity wymagaja otwarcia aplikacji tak samo. Jedno dotkniecie przed jazda.
- **Nie twierdzi, ze bedzie szybciej.** Ta zmiana kupuje **rozmowe**, nie predkosc; skrocenie petli
  zostaje osobnym zadaniem (2.7 w `poc-carplay-command`) i ma wlasny pomiar.
