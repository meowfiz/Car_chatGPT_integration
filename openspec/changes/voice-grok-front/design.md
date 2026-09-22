# Design: front glosowy Grok Voice + MCP

## Uklad calosci (i gdzie konczy sie ta zmiana)

```
kierowca (polski, CarPlay)
   |
   v
Grok Voice  ---- MCP (konektor) ---->  poc/grok_mcp.py        <-- TA ZMIANA, cienka warstwa
   ^                                        |
   |                                        v
   +---- mowi odpowiedz -----------  POST /api/agent/chat  (orchestrator, project_integration)
                                            |
                        +-------------------+--------------------+
                        v                                        v
              ask_core.ask (read-only)                 execute_worker (zapis, bramki,
              repozytoria, swiezosc                    galaz orch/<n>, testy, PR)
```

Wszystko na prawo od `grok_mcp.py` **juz istnieje i dziala**. Ta zmiana dodaje wylacznie lewa
kolumne. Kazda linia kodu, ktora zaczelaby tu decydowac „o co kierowcy chodzi", jest bledem
projektowym — ta decyzja nalezy do orchestratora i ma tam swoje testy.

## Decyzja 1: dlaczego dwa narzedzia (`ask` + `get_reply`), a nie jedno

Jedno wywolanie MCP musialoby zwrocic odpowiedz w czasie, ktorego nie mamy: zmierzona mediana
`claude -p` to **14,1 s**, ogon do **34,5 s**, a zlecenie zmieniajace kod to minuty. Klient
glosowy zerwie polaczenie wczesniej. Dlatego:

- `ask(session, text)` -> natychmiast `{"status": "working", "token": ...}`,
- `get_reply(session)` -> `{"status": "working"}` albo `{"status": "done", "text": ...}`.

To jest ten sam wzorzec, ktory `talk-to-claude-code` nazywa warunkiem uzywalnosci klienta:
**klient musi odpytywac w petli**. Grok to robi; klient, ktory poprzestaje na pierwszym „working",
nie nadaje sie i nie bedziemy tego obchodzic po stronie serwera.

Konsekwencja dla promptu narzedzia: opis `get_reply` musi **wprost kazac** wolac je ponownie,
dopoki status to `working` — to jedyne miejsce, gdzie zachowanie klienta zalezy od naszego tekstu.

## Decyzja 2: stan rozmowy trzymamy my

Klient glosowy daje nam identyfikator sesji i nic wiecej. Historia tur musi lezec po naszej
stronie, inaczej „a co z tym drugim projektem" nie znaczy nic. Trzymamy **n ostatnich par
(pytanie, odpowiedz)** na sesje, w pamieci procesu, z wygasaniem.

Czego tu swiadomie NIE robimy: nie budujemy trwalej bazy rozmow. Rozmowa w aucie ginie razem
z procesem i to jest w porzadku — trwaly slad pracy powstaje tam, gdzie zawsze: w commicie,
notatce sesji i logu. Gdyby okazalo sie potrzebne, to osobna zmiana, nie dopisek tutaj.

Ile tur? **Do zmierzenia (zadanie 4.3)**, nie do zgadniecia: kazda tura w promptcie kosztuje czas
odpowiedzi, a cel „rozmowa" konkuruje z celem „15 s". Wartosc poczatkowa 3 pary jest zalozeniem
roboczym, nie wynikiem.

## Decyzja 3: Funnel, czyli gdzie lezy prawdziwe ryzyko

Konektor MCP klienta chmurowego **nie wejdzie do tailnetu** — musi dostac publiczna, stabilna
nazwe hosta. `talk-to-claude-code` uzywa do tego Tailscale Funnel i to jest wlasciwy wybor
(stabilna nazwa, TLS, bez wlasnego certyfikatu). Ale to zmienia model zagrozen o klase:

| dotad | po tej zmianie |
|---|---|
| most slucha tylko na adresie Tailscale, z internetu niewidoczny | endpoint jest **publiczny**, chroniony wylacznie tokenem |
| sekret w sciezce wystarczal, bo sciezki nikt z zewnatrz nie widzial | token w sciezce jest **jedyna** bariera i wycieka do logow posrednikow |

Dlatego ta zmiana **wymaga** trzech rzeczy, zanim Funnel zostanie wlaczony (zadania grupy 3):

1. **Domyslnie tylko odczyt.** Narzedzie zapisujace jest osobne, wylaczone przelacznikiem, i idzie
   przez istniejacy `execute_worker` z jego bramkami (czyste drzewo, testy, zero usuniec, limit
   plikow z `.claude/orchestrator.json`) — nigdy „obok" nich.
2. **Limit tempa i log kazdego wywolania**, tak jak w `ask_server.py` dzis.
3. **Potwierdzenie glosem przed kazdym zapisem** — mechanizm, ktory bramka glosowa juz ma
   („Mam to wykonac w X?" + „tak"). Kopiujemy zachowanie, nie kod.

Czwarta rzecz, ktorej nie da sie zalatwic konfiguracja: **posrednie prompt injection**. Tresc
repozytoriow wraca do modelu chmurowego, a model chmurowy steruje naszymi narzedziami. Wniosek
jest ten sam co w researchu z 14.09: narzedzie wykonawcze przyjmuje **polecenia z zamknietej listy
orchestratora**, nigdy dowolnego tekstu do wykonania.

## Decyzja 4: co robimy z otwartymi sesjami na maszynie

Cel uzytkownika („rozmawiac z sesjami otwartymi na aktywnym komputerze") rozbija sie o platforme.
Stan wiedzy, zmierzony 2026-09-17 w `monitor/live_sessions.py` i uzupelniony 2026-09-22:

| operacja | mozliwa? | czym |
|---|---|---|
| wyliczyc otwarte okna (pid, cwd, busy/idle, sessionId) | **tak** | `claude agents --json`, bez TTY |
| wstrzyknac prompt do zywego okna interaktywnego z CLI | **nie** | brak skrzynki dla TTY |
| kontynuowac **kontekst** sesji | tak, warunkowo | `claude -p --resume <id>`, **tylko gdy idle**; przeciw zajetej forkuje kopie (ryzyko 2.7) |
| uruchomic / zatrzymac prace w tle | tak | `claude --bg`, `agents --json`, `logs`, `stop` (`monitor/sessions.py`) |
| rozmawiac z zywa sesja **z telefonu** | **tak, ale tylko recznie** | `/remote-control` -> claude.ai/code albo aplikacja Claude; **bez API, bez CarPlay** |

Stad zakres tej zmiany: front glosowy rozmawia z **wlasna** sesja mostu, a o cudzych oknach
potrafi **powiedziec**, co robia i czy sa zajete (narzedzie `sessions`, tylko odczyt, dane
z `live_sessions.py`). Dispatcher, ktory kontynuuje bezczynne okno, jest osobna zmiana i osobna
decyzja — nie przemycamy go tutaj.

## Decyzja 5: co z `poc/ask_server.py`

Zostaje jako sciezka zapasowa dla Skrotu iOS (`/voice/ask`, `/voice/reply` daja ten sam ksztalt
bez MCP) i **nie dostaje nowych funkcji**. Jego rdzen ma zniknac na rzecz `ask_core` w zmianie
`ask-core-client`; dublowanie logiki pytania w trzecim miejscu byloby powtorzeniem bledu, ktory
`ask_core` wlasnie naprawil.

## Ryzyka, ktore zapisujemy teraz, zeby nie udawac potem

- **Zaleznosc od cudzego klienta.** Gdy Grok zmieni zachowanie konektorow w glosie, front padnie
  bez naszego udzialu. Sciezka zapasowa (punkt 4 propozycji) jest dokladnie na to.
- **Subskrypcja.** Bez platnego planu Grok-a nie ma „Bring Your Own MCP".
- **Prywatnosc.** Fragmenty notatek i stanu repozytoriow wychodza poza tailnet do xAI. To jest
  cena rozmowy i ma byc powiedziana wprost, a nie odkryta pozniej.
- **Brak slowa budzacego** — ograniczenie iOS 26.4, wspolne dla wszystkich klientow glosowych
  w CarPlay. Jedno dotkniecie przed jazda i tyle.
