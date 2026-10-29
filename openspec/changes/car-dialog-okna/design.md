## Context

Zmierzone 2026-10-29 w kodzie huba (nie z pamięci):

- `_car_dispatch` (voice_gateway.py:4774): `session_id` + `project` + `prompt`; stan to `{project, ts, last_text}`
  w `~/.claude/carplay_sessions.json`, TTL 600 s; `parse_car_prompt` wyłapuje nazwę projektu na początku zdania.
  Wysyłka tylko do tmux **tej** maszyny (`cb.type_into`), czekanie synchroniczne 30 s, potem „pracuje jeszcze".
- `_ask_text_inner` (voice_gateway.py:4970): ścieżka domowa; `voice_brief.wants_status` + `find_project` =
  pytania o projekty z mierzonym stanem (monitor `/api/state`); sesja tmux `voice` z `voice_history`.
- `voice_escalate.start_escalation`: pytanie o szczegół projektu idzie do bezczynnego okna / kolejki ask,
  odpowiedź asynchronicznie przez HA `script.odpowiedz_asystenta`.
- `send_task.py` + bridge relay `/task`: wpisanie tekstu do okna na **innej** maszynie (jednokierunkowo).
- Monitor `/api/state`: per repo `machine`, `state` (working/idle), `task_current`; `active_machines`
  = `DESKTOP-FFSHIOA`, `DESKTOP-GEIH38C`. Okno otwarte na maszynie widać jako sesję tmux
  (`cb.running_sessions()` lokalnie).
- HA: 9 intentów + wildcard `{pytanie}` + stałe frazy; auto zna tylko to, co wyłapie Speech-to-Phrase.

Wniosek: transport, odmowy, tokeny i źródło stanu istnieją. Brakuje **jednej warstwy decyzji** (co to za
wypowiedź i gdzie jest użytkownik) oraz trzech rzeczy w transporcie: okno na drugiej maszynie z odpowiedzią,
kolejka na okno, asynchroniczna odpowiedź w oknie zajętym.

## Goals / Non-Goals

**Goals**
- Rozmowa jak w jednym oknie: mówię, gdzie chcę być; potem mówię, co chcę; „gdzie jestem" zawsze odpowiada.
- Minimum ograniczeń: brak sztywnej składni poza kilkoma słowami-kluczami na początku zdania; brak twardego
  wygasania stanu; wszystko, co nie jest komendą dialogu, trafia do bieżącego miejsca.
- Pamięć: rozmowa główna pamięta, że była w oknie i co się tam stało; okno pamięta swoje.
- Jedno źródło prawdy o projektach (to samo w aucie i w domu).

**Non-Goals**
- Nowe STT/TTS, nowa aplikacja, wejście inne niż HA Assist w CarPlay (decyzja D10 z `carplay-okna-projektow`).
- Zatwierdzanie uprawnień w oknie z auta (nadal niemożliwe; `should_refuse_car` zostaje).
- Streaming `Glosowo:` w trakcie pracy okna (Iter D z notatki 2026-10-13, warunkowa po pomiarze).

## Decisions

### D1. Maszyna stanów per `session_id`, logika w czystym module

`tools/car_dialog.py` (hub): `decide(state, text, world) -> (action, new_state)` bez I/O. `world` to
migawka: nazwy projektów + aliasy, które okna są otwarte na której maszynie i czy zajęte, domyślna maszyna.
`voice_gateway` robi tylko I/O wg `action`. *Dlaczego:* ZASADY 4.5 - decyzja w małej funkcji czystej da się
przetestować tabelą wypowiedzi i mutacją; zakopana w handlerze nie.

Stan (`carplay_sessions.json`, pola dodane do istniejących, zgodne wstecz):

```
mode: "main" | "window"
window: {project, machine}          # gdy mode=window
pending: {kind: "machine"|"project", options: [...], project?, ts}   # pytanie zwrotne
trail: [{project, machine, ts, last_text}]   # ostatnie 5 okien, do "wróć do poprzedniego"
last_text, ts
```

Przejścia:

```
main    --"przejdz do X"-->        window(X, M)        (pending, gdy M niejednoznaczne)
window  --"przejdz do Y"-->        window(Y, M')       (poprzednie na trail)
window  --"wroc" / "rozmowa glowna"--> main            (streszczenie okna do historii glownej)
*       --"gdzie jestem"-->        bez zmiany stanu
*       --"jakie projekty pracuja"-> bez zmiany stanu, odpowiedz z voice_brief
main    --inne-->                  rozmowa glowna (sciezka domowa, voice session)
window  --inne-->                  kolejka okna X@M
pending --odpowiedz-->             window(...) albo main; inna wypowiedz anuluje pending
```

### D2. Gramatyka komend: krótka, na początku zdania, tolerancyjna

Dopasowanie po `voice_brief.plain` (bez diakrytyków), tylko **na początku** wypowiedzi, żeby zdanie do okna
zaczynające się od zwykłego słowa nie zostało połknięte:

| komenda | zaczyna się od |
|---|---|
| przejście | `przejdz do`, `przelacz na`, `wejdz do`, `do okna`, `otworz okno` + nazwa [+ `na komputerze w pracy/w domu`, `w pracy`, `w domu`] |
| powrót | `wroc`, `wyjdz z okna`, `rozmowa glowna`, `koniec okna` |
| gdzie jestem | `gdzie jestem`, `gdzie pracujemy`, `w jakim oknie`, `gdzie my jestesmy` |
| projekty | rozpoznaje `voice_brief.wants_status` (to samo co w domu), także w oknie, gdy zdanie zaczyna się od `jakie projekty`, `co slychac`, `status` |
| powtórka | `powtorz`, `jeszcze raz` |
| poprzednie | `wroc do poprzedniego`, `poprzednie okno` |
| wymuszenie | `powiedz oknu <tekst>` / `do okna: <tekst>` wysyła dosłownie, gdyby tekst zaczynał się od słowa-klucza |

Nazwa projektu: `find_project` + aliasy (`poc/aliases.json`) + `okna.resolve` (4 poziomy); zdanie typu
„przejdź do car integration" rozstrzyga ten sam kod co dziś. Wątpliwość (2+ trafienia) = `pending(project)`:
„który: A czy B?". Odpowiedź „pierwszy / drugi / nazwa".

Odrzucone: klasyfikator LLM do intencji (opóźnienie 1-5 s w aucie, ZASADY „prosty system głosowy"; zasada jest
na tyle krótka, że LLM nie wnosi nic, a psuje przewidywalność).

### D3. Wybór maszyny: bez pytania, gdy jest oczywisty

Reguła w kolejności:

1. Jawnie w zdaniu („w domu", „na komputerze w pracy") -> ta maszyna.
2. Okno otwarte na dokładnie jednej maszynie -> ta.
3. Okno otwarte na obu -> **pytanie** „w pracy czy w domu?" (`pending(machine)`); wybór zapamiętany dla
   projektu do końca dnia (kolejne wejścia bez pytania).
4. Okno zamknięte wszędzie -> otwórz na maszynie domyślnej (praca), jeśli online; inaczej na drugiej;
   komunikat „otwieram X w pracy" (`okna.py <projekt>`, ten sam mechanizm co `mail_window`).
5. Maszyna offline -> wymieniona wprost: „komputer w pracy nie odpowiada, otworzyć w domu?" (`pending`).

Domyślna maszyna i nazwy mówione („w pracy" = DESKTOP-GEIH38C, „w domu" = DESKTOP-FFSHIOA) w
`~/.claude/car_dialog.json` (dane, nie kod). *Dlaczego pytanie tylko w przypadku 3:* użytkownik chce
domyślnie pracę i pyta się go tylko wtedy, gdy rzeczywiście są dwie opcje.

### D4. Transport do okna: dwa adaptery, jedna kolejka

`WindowTransport` z metodami `is_open`, `is_busy`, `open`, `send(text) -> handle`, `reply(handle, timeout)`.

- `LocalTmux` = dzisiejszy kod (`cb.type_into`, `capture`, `extract_reply`, `spoken_lines`, `is_busy`).
- `RemoteRelay` = `send_task.send_to_bridge` (POST `/task`) + odczyt odpowiedzi. **Otwarte (O1):** czy relay
  ma dziś odczyt panelu/odpowiedzi; jeśli nie, hub dokłada `GET /reply?project=&since=` (taka sama logika
  `extract_reply`/`spoken_lines`). Do czasu pomiaru okno zdalne działa tylko w trybie asynchronicznym (D5).

Kolejka FIFO per `(maszyna, projekt)` w pamięci bramki, **z odtworzeniem po restarcie z dziennika** (restart
bramki przy aktualizacji nie gubi polecenia; ZASADY 2.14 mówi, że restarty się zdarzają).

### D5. Odpowiedź: synchronicznie, gdy szybka, inaczej asynchronicznie

Budżet synchroniczny `CAR_SAY_SYNC_S` = 25 s (dziś 30). Odpowiedź przed upływem budżetu wraca w `text`.
Po budżecie: `outcome="queued"`, `text` = „okno X pracuje, powiem, gdy skończy", a gdy `Glosowo:` dojdzie
(lub okno skończy), bramka woła HA `script.odpowiedz_asystenta` (ten sam kanał co `voice_escalate`, adresat =
satelita tej rozmowy). Zajęte okno: polecenie ląduje w kolejce, komunikat „po bieżącym zadaniu".
Każdy komunikat krótki (<= 2 zdania, ZASADY 7.6), nazwa okna tylko przy zmianie miejsca lub po pytaniu.

### D6. Kontekst i historia

- Rozmowa główna: bez zmian (sesja tmux `voice` + `voice_history.append`). Na „wróć" bramka dopisuje do
  `voice_history` parę `Q: [okno X] ...` / `A: <ostatnie 1-2 Glosowo z okna>`, więc kolejne pytanie główne
  „a co tam z X?" ma kontekst.
- Okno: własna sesja Claude Code (pamięć w oknie). Pierwsza wiadomość po wejściu nie dostaje wstrzykniętego
  kontekstu (okno zna swoją pracę); wstrzyknięcie tylko na prośbę („powiedz oknu, o czym rozmawialiśmy").
- `car_trail.jsonl` (bramka, dopisywany): `{ts, session_id, mode, project, machine, q, a}`. Źródło dla „gdzie
  jestem", „wróć do poprzedniego", pomiaru i `Co robiliśmy w oknie X` (`voice_brief`-style czytanie dziennika).
- **Brak twardego wygasania stanu** (dziś 600 s). Stan trzymany 4 h ciszy; przy pierwszej komendzie po przerwie
  bramka mówi, gdzie jest („Jesteś nadal w oknie X"), zamiast cicho wracać do głównej (R3 z poprzedniej
  zmiany: nie udawać pamięci, której nie ma - tu pamięć jest, więc ją pokazujemy).

### D7. „Gdzie jestem" jest zawsze mierzone

Odpowiedź składa się z: trybu (główna/okno), projektu i maszyny, czy okno pracuje/bezczynne i od kiedy
(`/api/state` + `is_busy`), ostatniego `Glosowo:` okna (skrót), długości kolejki. Przykład:
„Jesteś w oknie project integration na komputerze w pracy; pracuje od 4 minut nad zleceniem interfejsu auta."
Brak danych = powiedziane („nie widzę stanu okna"), nie zgadnięte (ZASADY 5.15).

### D8. Bezpieczeństwo w aucie

`should_refuse_car` działa **przed** rozstrzygnięciem dialogu, na każdej wypowiedzi. Okno przejęte z auta nie
potwierdza uprawnień; polecenie, które w oknie wymaga zgody, kończy się komunikatem „okno czeka na zgodę, zrób
to z komputera" (wykrycie monitem w panelu, `cb.is_busy`/wzorzec „Do you want to"), nie wisi w ciszy.
Token Bearer bez zmian. Przejście do okna zdalnego nie omija odmów po stronie bramki.

### D9. Rozdział pracy

| okno | zakres |
|---|---|
| **Car_chatGPT_integration** (tu) | ta zmiana, kontrakt HTTP, scenariusze e2e (tabela wypowiedzi), pomiar w aucie, notatki |
| **project_integration** | `car_dialog.py`, `/api/car/say`, kolejka, adapter zdalny, dziennik, testy jednostkowe + mutacje |
| **HA** | jeden intent `claude {pytanie}` -> `rest_command car_say`; usunięcie / przekierowanie 9 intentów; odpowiedź asynchroniczna; pytanie O2 poniżej |

## Risks / Trade-offs

- **R1. Słowo-klucz połknie zdanie do okna** („wróć do pierwszego akapitu"): komenda tylko na początku zdania
  i tylko w ścisłej formie; „powiedz oknu ..." wymusza dosłowne wysłanie. Test: wypowiedzi graniczne w tabeli e2e.
- **R2. Okno zdalne bez odczytu odpowiedzi** (O1): bez niego dialog z oknem w domu jest tylko asynchroniczny.
  Mitygacja: wynik pomiaru przed zakresem; w najgorszym razie „wysłane do okna w domu" bez treści odpowiedzi.
- **R3. Dwie rozmowy naraz** (telefon + auto): stan jest per `session_id`, więc nie zderzają się; kolejka okna
  jest wspólna, kolejność = kolejność wysłania.
- **R4. Speech-to-Phrase** nie rozpozna dowolnego zdania: wildcard `{pytanie}` w HA jest już w użyciu; O2
  sprawdza, czy da się uniknąć słowa „Claude" na początku (zastępczy agent konwersacji w HA).
- **R5. Wstrzyknięcie do okna przez treść z auta**: polecenie jest zwykłym tekstem użytkownika (`[glos-ha]`),
  tak jak dziś; nic nowego nie wchodzi z zewnątrz poza STT.

## Open Questions

- **O1** (hub): czy relay ma odczyt odpowiedzi okna na drugiej maszynie. Pomiar jednym poleceniem, zanim
  powstanie adapter.
- **O2** (HA): czy da się ustawić gateway jako zastępczego agenta konwersacji (`conversation.process` fallback),
  żeby wyrzucić prefiks „Claude"; jeśli nie, prefiks zostaje i stan okna go nie wymaga po stronie bramki
  (bramka toleruje wypowiedź bez prefiksu, bo HA go odcina).
- **O3**: nazwy mówione maszyn („w pracy", „w domu") - potwierdzić z użytkownikiem przy pierwszym teście.
