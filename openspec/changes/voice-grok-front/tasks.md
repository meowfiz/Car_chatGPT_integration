## 1. Warunki wstepne i porzadki (zanim powstanie kod)

- [ ] 1.1 Potwierdzic plan Grok-a z „Bring Your Own MCP" i zapisac, ktory to plan i co kosztuje; bez tego cala grupa 3 jest bezprzedmiotowa i zostaje sciezka zapasowa
- [ ] 1.2 Przeczytac `osaighi/talk-to-claude-code` w calosci i spisac w `notes/research/`, co bierzemy (wzorzec `ask`/`get_reply`, endpointy `/voice/*`, Funnel), a czego nie (ich most do sesji — my mamy orchestrator); **nie kopiowac kodu bez przeczytania licencji**
- [ ] 1.3 Zmierzyc, czy orchestrator na pececie odpowiada na `POST /api/agent/chat` z tej maszyny i ile to trwa (3 proby, mediana) — to jest baza czasowa, wobec ktorej liczymy koszt frontu
- [ ] 1.4 Zaktualizowac naglowek `monitor/live_sessions.py`: wniosek „nie da sie wejsc do zywego okna" jest prawdziwy **dla CLI**, ale Remote Control (`/remote-control`, Pro/Max/Team/Enterprise) podlacza zywa sesje do claude.ai/code i aplikacji mobilnej — **recznie, bez API i bez CarPlay**. Zapisac obie polowy, zeby nikt nie szukal drugi raz
- [ ] 1.5 Zapisac w `notes/HANDOFF_most_pytan.md` podzial rol: Remote Control = telefon w reku, ten front = auto; to nie sa konkurenci

## 2. Serwer MCP jako cienka warstwa

- [ ] 2.1 `poc/grok_mcp.py`: narzedzia `ask(session, text)` i `get_reply(session)`; `ask` wraca natychmiast ze statusem `working`, `get_reply` oddaje `working` albo `done` z tekstem
- [ ] 2.2 Opis narzedzia `get_reply` **wprost** instruuje klienta do ponownego wywolania przy statusie `working` (to jedyne miejsce, gdzie zachowanie klienta zalezy od naszego tekstu)
- [ ] 2.3 Kazde zapytanie idzie do `POST /api/agent/chat` orchestratora; **zero wlasnego promptu, zero `claude`, zero wlasnej listy repo**
- [ ] 2.4 Test nazywajacy porazke: plik `grok_mcp.py` nie zawiera wywolania `claude` ani sciezek repozytoriow — mutacja (dopisac `subprocess.run(["claude", ...])`) ma go wywalic
- [ ] 2.5 Historia rozmowy: n ostatnich par na sesje, wygasanie, izolacja miedzy sesjami; test: dwie sesje nie widza swoich tur
- [ ] 2.6 Narzedzie `sessions` (tylko odczyt) na danych z `monitor/live_sessions.py`: repozytorium + zajete/bezczynne; test: prosba o zmiane w zajetym oknie konczy sie odmowa, nie forkiem
- [ ] 2.7 Endpointy zapasowe `/voice/ask` i `/voice/reply` z tokenem w sciezce i w query (Skroty iOS nie ustawiaja naglowkow); ten sam przebieg co przez MCP

## 3. Wystawienie publiczne — dopiero po bramkach

- [ ] 3.1 Limit tempa i log kazdego wywolania (wzorzec z `poc/ask_server.py`), zanim cokolwiek wyjdzie poza tailnet
- [ ] 3.2 Zapis **domyslnie wylaczony**; wlaczony idzie wylacznie przez `execute_worker` z jego bramkami i z potwierdzeniem glosem — bramki SHALL NOT byc omijane; test odmowy przy wylaczonym zapisie
- [ ] 3.3 Tailscale Funnel ze stabilna nazwa hosta; zapisac nazwe i sposob odtworzenia w HANDOFF
- [ ] 3.4 Test bezpieczenstwa: zly token -> 403 i wpis w logu; brak tokenu -> 403; token w query dziala tak samo jak w sciezce
- [ ] 3.5 Zapisac wprost w HANDOFF, ze od tego momentu endpoint jest **publiczny**, oraz co z repozytoriow wychodzi do xAI (prywatnosc jako decyzja, nie odkrycie)

## 4. Prerejestracja i pomiar rozmowy

- [ ] 4.1 PREREJESTRACJA (przed pierwszym przebiegiem, ZASADY 3.3): **hipoteza** — rozmowa wieloturowa utrzymuje kontekst przez >= 4 tury w >= 8/10 przebiegow, a czas do pierwszego slowa odpowiedzi ma mediane <= 20 s; **dane** — 10 rozmow po 5 tur, scenariusze spisane z gory, na postoju; **etykieta** — tura udana = odpowiedz zgodna z danymi monitora i odnoszaca sie do wlasciwej tury wczesniejszej; **jedna statystyka** — odsetek rozmow z zachowanym kontekstem do 4. tury; **liczba testowanych porownan: 2** (liczba tur w historii: 3 wobec 5); **poprawka na wielokrotnosc** — przy dwoch porownaniach raportujemy obie liczby, nie wybieramy lepszej po fakcie; **konfuzje** — dlugosc odpowiedzi orchestratora i to, czy klient rzeczywiscie odpytywal w petli (z logu); **warunek NEGATYWU** — jesli klient przestaje odpytywac przed koncem w > 2/10 przebiegow, front jest nieuzywalny i wracamy do sciezki zapasowej; **czego wynik NIE uprawnia** — nie mowi nic o jezdzie, o hasach w tle ani o zleceniach zapisujacych
- [ ] 4.2 Przebieg wg 4.1 na postoju; tabela do `notes/HANDOFF_most_pytan.md`
- [ ] 4.3 Liczba tur w historii wybrana **pomiarem** (3 wobec 5), nie zalozeniem; zapisac koszt czasowy kazdej dolozonej tury
- [ ] 4.4 Jazda: >= 10 tur, >= 3 rozne tematy, >= 3 tury przy predkosci >= 70 km/h; kazda nieudana tura przypisana do warstwy (klient / siec / orchestrator / model / odtwarzanie)
- [ ] 4.5 Wynik negatywny zapisac jako negatywny z przyczyna (ZASADY 5.8) — takze wtedy, gdy przyczyna lezy po stronie Grok-a

## 5. Decyzja

- [ ] 5.1 Wpis „Decyzja" w HANDOFF z liczbami: czy rozmowa w aucie dziala, na czym stoi, co kosztuje (subskrypcja, publiczny endpoint, prywatnosc), i czy `poc/ask_server.py` mozna wygasic
- [ ] 5.2 Aktualizacja `notes/start.md`, notatka sesji, `python notes/gen_openspec_status.py`
