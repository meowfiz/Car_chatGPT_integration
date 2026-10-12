## Context

Trzy cegły już są w `project_integration` (zmierzone 2026-10-12 agentem Explore):

- **Mapa projektów**: `~/.claude/monitor_repos.env` (22 wpisów `NAZWA=sciezka`), czytana
  przez `project_integration/tools/okna.py:59` (`parse_repos()`).
- **Fuzzy match nazwy**: `okna.resolve()` w tym samym pliku (`okna.py:77`) — exact → prefix
  → substring, ignoruje wielkość liter i znaki.
- **Transport promptu do tmux**: `project_integration/monitor/cli_bridge_reap.sh:288` —
  `tmux send-keys` (escape, ctrl-u, tekst, enter). Nazwa sesji = `tmux_name(projekt)`
  z `okna.py:151`.
- **Bramka głosowa** na porcie 8788 (`project_integration/monitor/voice_gateway.py`,
  endpoint `/voice/ask`), ekstraktor `spoken_summary()` (linia 408) biorący ostatnie
  wystąpienie `Glosowo:` z odpowiedzi. Silniki TTS: Chatterbox / VCC / edge-tts, wybór
  w `~/.claude/voice_choice.json`.
- **Zero kodu CarPlay/Siri w jakimkolwiek repo** poza wzmianką w `monitor/ask_core.py:163`.

Istniejąca zmiana `poc-carplay-command` (7/39 tasks) zakłada one-shot `claude -p` z dostępem
tylko do odczytu — **inny przepływ**: w aucie użytkownik dostaje odpowiedź modelu, ale nie
rozmawia z sesją Claude Code, która już otworzyła projekt. Ta zmiana domyka ten brakujący
tryb.

**Ograniczenie z twardej rzeczywistości**: Siri w CarPlay dla iOS 17 nie mówi po polsku (patrz
proposal `poc-carplay-command`), więc dyktowanie i odczyt idą przez Whispera + edge-tts/VCC,
dokładnie jak w PoC. Nie powtarzamy tej analizy — dziedziczymy.

## Goals / Non-Goals

**Goals:**

- Powiedzieć w aucie „projekt car integration — dodaj test do parsera" i mieć prompt wrzucony
  do uruchomionej sesji Claude Code tego projektu w tmux, bez dotykania ekranu.
- Dostać `Glosowo:` tej sesji z powrotem przez głośnik auta w ≤ 30 s mediany (próg do
  prerejestracji — por. `poc-carplay-command 5.1`).
- Reuse całej infrastruktury `project_integration` — zero duplikacji fuzzy match, TTS,
  rejestru projektów.
- Rejestr aktywnej sesji: po jednym „projekt X" kolejne komendy idą tam, aż użytkownik
  powie inną nazwę albo minie 10 min ciszy.

**Non-Goals:**

- Pisanie od zera parsera nazw projektów (reuse `okna.resolve`).
- Pisanie od zera TTS, Whispera, bramki głosowej (reuse `voice_gateway`).
- Wywoływanie `/opsx:apply`, `/skill` czy innych meta-komend z auta — Claude w sesji
  tmux dostaje zwykły prompt; cokolwiek robi dalej, robi normalnie.
- Rozmowa wieloturowa z pamięcią kontekstu po stronie bramki — kontekst żyje w samej
  sesji Claude.
- Otwieranie nowych okien projektów głosem w pierwszej iteracji (musi istnieć — reguła
  bezpieczeństwa: w aucie nie da się zatwierdzić uprawnień). Zostawiamy to na iterację
  drugą po PoC.

## Decisions

### D1. Nowy endpoint `POST /api/car/command` w `voice_gateway.py`, nie osobny proces

Bramka już trzyma TLS tailnetowy, Whisper, kolejkę TTS i mostek `Glosowo:`. Osobny proces
= drugi certyfikat, drugi port, drugi watchdog, duplikacja. Alternatywa (osobny mikroserwis
`car_dispatch.py`) odrzucona, bo jedyny zysk to „czystość modułu"; koszt — infrastruktura
dubluje się, a stan projektu (świeżość `Glosowo:` z tmux) i tak musi widzieć bramka,
żeby odtworzyć audio.

### D2. Dyspozycja promptu przez `tmux send-keys`, nie przez named pipe

`cli_bridge_reap.sh` to robi od miesięcy w sposób znoszący polskie znaki, ctrl-c i długie
linie (`cli_bridge_reap.sh:288`). Reuse tego samego kodu (wywołanie z Pythona przez
`subprocess` do `tmux send-keys -t <sesja>:0 -l <tekst>` + `C-m`). Alternatywa (named pipe
w `~/.claude/okna/<projekt>.pipe`) odrzucona — wymaga modyfikacji Claude Code, żeby czytał
pipe równolegle ze stdin, a tego nie zrobimy.

### D3. Rejestr aktywnej sesji CarPlay w pliku JSON, nie w pamięci bramki

Bramka restartuje się przy każdej aktualizacji (`ready.py` → `services.py --restart`).
Trzymanie w pamięci znaczy „po pierwszej aktualizacji w ciągu dnia zapominamy, który projekt
jest aktywny" — niewidoczne, dopóki nie zepsuje jazdy. Plik `~/.claude/carplay_sessions.json`
z sekcją per `session_id` (UUID z Siri Shortcut), ostatni projekt + unix ts. Odczyt / zapis
pod `fcntl` locku (reuse `monitor/lockutil.py` z `project_integration`).

### D4. Rozróżnienie promptu i wyboru projektu — prefiks „projekt X[: ]"

Parser rozpoznaje trzy formy wejścia (po transkrypcji Whisper):

1. `projekt <nazwa>` (nic więcej) → ustaw aktywną sesję, odpowiedź `Glosowo: ok, projekt
   <pelna_nazwa>`.
2. `projekt <nazwa>: <reszta>` → ustaw aktywną sesję + wrzuć resztę do tmux.
3. tylko `<reszta>` → wrzuć do aktualnej aktywnej sesji; jeśli brak aktywnej → `Glosowo:
   nie wiem, do którego projektu; powiedz: projekt <nazwa>`.

Dwukropek jest **opcjonalny** — Whisper go nie wstawia zwykle, więc fallback: pierwsze słowo
po „projekt" to kandydat, drugie + reszta to prompt, jeśli pierwsze słowo jednoznacznie
rozwiązuje się do istniejącego projektu. Alternatywa (NLU przez `claude -p` do klasyfikacji
intencji) odrzucona — koszt latencji, a reguła jest tak prosta, że LLM to overkill.

### D5. Fuzzy match przez `okna.resolve()` wymusza jednoznaczność, inaczej dialog

`okna.resolve()` zwraca listę. Jeden wynik → wykonanie. Dwa i więcej → `Glosowo: który —
<X> czy <Y>?` i oznaczenie sesji „pending resolution". Zero wyników → `Glosowo: nie znam
projektu <input>`. **Nic nie wysyłamy do tmux przed rozwiązaniem**, bo pomyłka trafia
w cudzą sesję.

### D6. Nasłuch na `Glosowo:` z pane — przez `tmux capture-pane`, nie przez stream

Po `send-keys` bramka woła w pętli `tmux capture-pane -t <sesja>:0 -p -S -200` co 500 ms,
szuka linii zaczynającej od `Glosowo:` **nowszej niż timestamp wysłania**. Odrzucone:
`tmux pipe-pane` do pliku — zapisuje całą historię pane, trudno odróżnić starą linię
`Glosowo:` od nowej.

### D7. Timeout 30 s + „pracuję jeszcze"

Po 30 s bez `Glosowo:` → odpowiedź `Glosowo: pracuję jeszcze, zapytaj za chwilę`. Sesja
oznaczona `pending`, kolejne polecenie bez zmiany projektu **najpierw** sprawdza pane
(może już jest). Alternatywa (push notification z telefonu, gdy skończy) odrzucona na
PoC — wymaga oddzielnego kanału APNs, który nie istnieje.

### D8. Odmowa poleceń pisujących jest robiona po stronie bramki

Lista słów kluczowych (`git push`, `git reset --hard`, `rm -rf`, `sudo`, `--force`,
`DROP TABLE`, `shutdown`, `reboot`) → `Glosowo: w aucie tego nie zrobię, zrób z telefonu`.
Powód: w aucie nie da się dotknąć ekranu. **To nie jest zamiennik ochron Claude** — to
dodatkowe sito, żeby model nie dostał nawet prośby. Alternatywa (polegać wyłącznie
na Claude) odrzucona, bo autostop ochrony Claude na `--dangerously-skip-permissions`
jest poza naszą kontrolą.

### D9. Siri Shortcut i Whisper — reuse PoC

Shortcut wygląda jak w `poc-carplay-command 3.1`: `Record Audio` o stałej długości → POST
→ `Speak Text` **zastąpiony** `Play Sound` z response body (`audio/mpeg`). Jeden plik
`.shortcut` z dołączoną instrukcją w `notes/HANDOFF_carplay_okna.md`. Alternatywa
(aplikacja natywna CarPlay) odrzucona — osobne zadanie na deweloperską licencję Apple,
a Shortcut wystarczy, co pokazał PoC pytania.

### D10. Zmiana wejścia: HA Assist w CarPlay, nie Siri Shortcut (decyzja 2026-10-12 po pomiarze)

**Co się zmieniło:** test w aucie wykazał, że Siri zamyka sesję audio Shortcuta zanim
`Odtwórz dźwięk` dokończy — użytkownik słyszał „test" i „test głosu w a..." zamiast
pełnego zdania. Diagnoza: Siri ma własny budżet audio, Shortcut nie dociąga długich
plików. Fallback Skrót B (`Przeczytaj tekst`) dociąga, ale głosem systemowym Siri
(polski Zosia), nie VCC. **Pomiar w kuchni z HA Assist (2026-10-12): pełne zdanie
twoim głosem Sznuka, bez cięć** — kafelek Assist w HA Companion w CarPlay jest już
dodany jako Quick Access.

**Nowy przepływ wejściowy** zamiast D1 (`POST /api/car/command` w voice_gateway):

1. Użytkownik dotyka **Home Assistant** w CarPlay → kafelek **Assist** → mówi.
2. HA pipeline PL (STT = Speech-to-Phrase, lokalnie na Pi) parsuje frazę przez
   `voice/claude_sentences_pl.yaml`.
3. Pasujący intent odpala `voice/rest_command_claude.yaml` — REST do bramki na pececie
   (ten sam host co voice_gateway, inny endpoint albo nowy).
4. Bramka woła `okna.resolve()` + `tmux send-keys` do istniejącej sesji projektu
   (tu D2, D3, D5–D8 bez zmian).
5. `capture-pane` czeka na `Glosowo:`, zwraca tekst (nie audio).
6. HA pipeline wymawia tekst przez swoje TTS (Piper lokalny lub VCC proxy) — twój
   głos, własna sesja audio HA, dociąga do końca.

**Co z D1 (/api/car/command w voice_gateway) i D4 (parser prefiksu „projekt" w Pythonie):**

- D1: zastąpione nowym endpointem **`POST /api/car/dispatch`** w bramce, który
  **przyjmuje już sparsowane pola** z HA (`project`, `prompt`, `session_id`) i **zwraca
  tekst** (`text/plain`), nie audio. Audio robi HA. Mniej kodu, bo cała STT i TTS
  zostaje w HA pipeline.
- D4: zastąpione **frazami w `voice/claude_sentences_pl.yaml`** po stronie HA (dostawca:
  HA Claude okno). Przykładowe frazy do uzgodnienia:
  `Claude, do okna <projekt>, <reszta>` / `Claude, w oknie <projekt>, <reszta>` /
  `Claude, otwórz okno <projekt>` / `Claude, kontynuuj`. Mapowanie nazw („car" →
  Car_chatGPT_integration) idzie przez aliasy w `voice/claude_aliases.yaml` (nowy),
  bo Speech-to-Phrase potrzebuje słownika z góry — nie da się fuzzy match po STT.

**Co zostaje bez zmian:**

- D2 (`tmux send-keys`), D3 (`carplay_sessions.json`), D5 (`okna.resolve()` jako
  weryfikacja nazwy — teraz tylko dla sanity check, bo HA już wybrało kandydata),
  D6 (`capture-pane` na `Glosowo:`), D7 (timeout 30 s), D8 (odmowa `rm -rf`/`git push`).

**Alternatywa (odrzucona po pomiarze):** utrzymać Siri Shortcut dla krótkich poleceń
i HA Assist dla długich. Odrzucone, bo (a) ograniczenie Siri jest niedeterministyczne —
czasem urwie przy 2 słowach, czasem przy 10; (b) dwie ścieżki = dwa parsery, dwa
mostki, podwójne odmowy; (c) HA i tak dowozi + ma własny głos. Siri zostaje tylko
w HANDOFF jako diagnostyczny `CarPlay audio test` do sprawdzania samego Tailscale.

**Rozdział pracy:** HA Claude pisze parser fraz (`voice/claude_sentences_pl.yaml` +
`claude_aliases.yaml` + intent `rest_command_claude`); ja aktualizuję specyfikację
i pisząc endpoint `/api/car/dispatch` + rejestr sesji + capture `Glosowo:` + odmowa.
Spotykamy się na kontrakcie HTTP: `POST /api/car/dispatch` body JSON `{session_id, project, prompt}`,
odpowiedź `{text, outcome}`.

## Risks / Trade-offs

**R1. Siri Shortcuts w CarPlay nie odtworzy `audio/mpeg` z HTTPS endpointu** → mitygacja:
pierwsze zadanie w `tasks.md` to zmierzyć to na postoju, 3 próby, zapis do HANDOFF.
Jeśli nie zadziała — fallback na `Speak Text` z tekstem w response (`X-Reply-Text` header,
tak dziś robi `voice_gateway`), ale **brzmi głosem systemowym, nie wybranym** — część
istotnego celu „jak w moim oknie" odpada. **Decyzja o rezygnacji z całości dopuszczalna
po R1 negatywnym.**

**R2. `tmux send-keys` do pane, w którym Claude jest w środku odpowiedzi, może przerwać
jego output** → mitygacja: przed wysłaniem sprawdź `tmux display-message -p -t <sesja>:0
'#{pane_in_mode}'` i ostatnią aktywność; jeśli pane „aktywny" (zmiana content w ostatnich
2 s) — opóźnij o 2 s albo odmów (`Glosowo: Claude jeszcze pisze, poczekam`). Trade-off:
czasem użytkownik świadomie chce przerwać — zrobi to drugim poleceniem.

**R3. Rejestr aktywnej sesji wygasa po 10 min i użytkownik w aucie nie wie** → mitygacja:
pierwsza komenda po wygaśnięciu, która NIE zaczyna się od „projekt", dostanie `Glosowo:
sesja wygasła, powiedz projekt X`. Nie udajemy pamięci, której nie ma.

**R4. Fuzzy match wybiera zły projekt przy nazwach podobnych** (np. „Car" vs „Car
chatGPT Integration") → mitygacja: `okna.resolve()` wymusza unikatowość — jeśli oba
pasują prefiksem/substringiem, dostaje dialog „który?". Dodatkowo: po pierwszym wyborze
sesja się „zapamiętuje", więc kolejne krótkie wezwania idą tam.

**R5. Whisper transkrybuje nazwę projektu błędnie** → mitygacja: `okna.resolve()` jest
tolerancyjny na substring + brak dialektyki (dolne znaki, spacje). Zapisujemy wszystkie
niezrozumiane wejścia do `project_files/run_files/carplay_misses.jsonl` — PoC dostarczy
listę do dostrojenia aliasów (`aliases.json` style, już używany w `poc/ask_server.py`).

**R6. Jazda w zasięgu LTE/5G, tailnet potrafi mignąć** → mitygacja: bramka ma już retry
po stronie klienta w `voice_gateway` + endpoint `/health`; Shortcut sprawdza najpierw
`/health` i jeśli brak w 2 s — mówi `Glosowo: brak sieci`.

**R7. Siri rozpoznaje „Projekt" jako polecenie dla innego skrótu / aplikacji CarPlay** →
**nieaktualne po D10** (porzucamy wejście przez Siri Shortcut). Zostawione w tekście jako
dziedzictwo wczesnej iteracji.

**R8. HA Assist pipeline PL potrafi utknąć** (STT Speech-to-Phrase, TTS Piper/VCC —
osobne usługi na Pi i w kuchni) → mitygacja: ping `curl` z pecetu do HA
`/api/assist_pipeline` przed każdym startem auta — jest już w `services.py --status`;
jeśli down → bramka na pececie zwraca na `/api/car/dispatch` kod 503 z `Glosowo: HA
usnęło, zbudź routerem`. Trade-off: użytkownik dowie się dopiero w aucie, że HA
padło — stąd test z kuchni **przed** jazdą (potwierdzony 2026-10-12).

**R9. Speech-to-Phrase łapie tylko frazy ze słownika — nazwa projektu musi być w
`claude_aliases.yaml`** (pod kontrolą HA Claude) → mitygacja: dodając nowy projekt do
`monitor_repos.env` dopisujemy też **wymawialny alias** do YAML HA (reguła dokumentacyjna,
nie techniczna — ZASADY 9 wymaga świadomego kroku). Alternatywa (OpenAI Whisper
w pipeline HA zamiast Speech-to-Phrase) odrzucona, bo HA ma w deklaracji „pełny offline"
(patrz `HA/handsoff.txt`). Przeniesienie Whispera do HA (lokalny, bez chmury) jest
możliwe, ale wychodzi poza zakres tej zmiany.

**R10. Kontrakt HTTP między HA a bramką pecetu wymaga odrębnej autoryzacji** — HA woła
REST, Siri nie wołało bezpośrednio → mitygacja: token w nagłówku `Authorization`
współdzielony między `rest_command_claude.yaml` (po stronie HA) a `/api/car/dispatch`
(po stronie pecetu). Token w `~/.claude/car_tokens.json` na obu maszynach; rotacja
ręczna, bez automatyzacji na PoC.

## Migration Plan

Zaktualizowana po D10 (2026-10-12). Kroki wczesnej iteracji (Siri Shortcut) zostaly
zrealizowane do punktu „zmierzone, odrzucone".

1. ✅ **Siri Shortcut PoC** (zadanie 1 w `tasks.md`): zmierzone 2026-10-12 — audio
   urywa sie, Siri zamyka sesje. Zapis w `notes/HANDOFF_carplay_okna.md`. Endpoint
   `/api/car/test-audio` **zostaje** jako diagnostyka Tailscale/certyfikatu.
2. ✅ **HA Assist w kuchni** (poza oryginalnym planem, dodane 2026-10-12 po R1-negative):
   HA Claude dodal kafelek Assist jako Quick Access w CarPlay, pipeline PL + VCC dowozi
   twoim glosem; potwierdzone na glosniku w kuchni, pelne zdanie.
3. **HA Assist w aucie — seria C pomiarowa** (zadanie 1.5.1 w `tasks.md`): 3 proby
   „test glosu w aucie" przez kafelek Assist w CarPlay. Oczekiwany wynik: pelne zdanie
   Sznuka z glosnika auta, bez ciec. Negatyw tutaj = CarPlay odcina rowniez HA sesje —
   wracamy do design.
4. **Kontrakt HTTP HA ↔ bramka pecetu**: `POST /api/car/dispatch` body JSON
   `{session_id, project, prompt}`, odpowiedz JSON `{text, outcome}` (`sent` /
   `ambiguous` / `missing` / `refused` / `timeout`). Nagłówek `Authorization: Bearer`.
   HA Claude pisze stronę HA (`rest_command_claude.yaml`), ja pisze bramke.
5. **Parser fraz w HA** (zadanie 1.5.2, HA Claude): rozszerzenie `voice/claude_sentences_pl.yaml`
   o „Claude, do okna <projekt>, <reszta>" / „Claude, w oknie <projekt>, <reszta>" /
   „Claude, otworz okno <projekt>" / „Claude, kontynuuj"; `voice/claude_aliases.yaml`
   mapuje wymawialne nazwy na klucze z `monitor_repos.env`. **Nie dotyka Speech-to-Phrase
   konfiguracji — tylko YAML dodatkowy.**
6. **Endpoint `/api/car/dispatch` w bramce** (zadanie 2.1 po D10): parsuje JSON, wola
   `okna.resolve()` (sanity), `tmux send-keys`, `capture-pane` na `Glosowo:`, zwraca
   JSON. Reuse `cli_bridge_reap.sh` sekwencji escape z D2. Testy jednostkowe w
   `project_integration/project_files/python/tests/test_car_dispatch.py`.
7. **Rejestr aktywnej sesji CarPlay** (zadanie 3.1 bez zmian wobec D3) — ale klucz
   sesji przychodzi od HA (`session_id` = conversation_id HA), nie od Siri Shortcut.
8. **Jazda pomiarowa** z prerejestracja (zadanie 6.1 bez zmian w metodzie, nowe
   wejscie): ≥ 10 prob, mediana ≤ 20 s, > 8/10 poprawnych nazw projektu.
9. **Rollback**: usunięcie endpointu `/api/car/dispatch` i wiersza w `rest_command_claude.yaml`;
   kafelek Assist zostaje (uzyteczny poza tym PoC); rejestr sesji w JSON mozna skasowac;
   diagnostyka `/api/car/test-audio` i `/api/car/test-text` ida wedlug task 7.1.

## Open Questions

- **Q1**: Który silnik TTS brzmi w aucie najlepiej (Chatterbox z Tailnetu vs lokalny
  edge-tts)? Pomiar w kroku 4 migracji — nie zgadujemy.
- **Q2**: Czy zmieniać model dyktowania (Whisper `medium` vs `large-v3`) dla polskiego
  w aucie? `poc-carplay-command 5.6` to zmierzy, dziedziczymy wynik — ta zmiana nie bierze
  tego na siebie.
- **Q3**: Co z poleceniami wymagającymi dialogu „yes/no" od Claude (np. `/opsx:apply`
  pyta o potwierdzenie)? Pierwsza iteracja — po prostu wrzucamy i oglądamy, co pisze
  w `Glosowo:`; jeśli pyta — druga komenda głosem „tak" trafi do pane. Druga iteracja
  może dodać specjalne polecenia „tak"/„nie" rozpoznawane przed send-keys.
- **Q4**: Jak traktować okno, które jeszcze nie istnieje — otworzyć czy odmówić? Decyzja
  **odmowa w PoC** (R6 w `What Changes`); otwieranie w drugiej iteracji po pomiarze
  bezpieczeństwa.
