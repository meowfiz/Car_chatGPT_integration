# HANDOFF — Endpointy bramki pod CarPlay / HA

**Kod**: `D:\claude_projekty\project_integration\tools\voice_gateway.py`
**Port**: `8788` (zmienna `ASK_VOICE_PORT`), TLS tailnet (certyfikat `tailscale cert`), bind na tailnet.
**Routing**: GET w `do_GET` (ok. linii 1670), POST w `do_POST` (ok. linii 2620).
**Base URL (przykład)**: `https://desktop-geih38c.taileb4004.ts.net:8788`

Wszystkie endpointy `/api/car/*` **oprocz** `test-audio` i `test-text` wymagaja `Authorization: Bearer <token>` i zwracaja `application/json; charset=utf-8` z polem `outcome` (enum: `sent | ambiguous | missing | refused | timeout | resolved`).

---

## Autoryzacja

- Plik: `~/.claude/car_tokens.json` (na pececie z bramka; HA trzyma ten sam token w secrets).
- Format minimalny:
  ```json
  {"token": "0123456789abcdef0123456789abcdef", "created": "2026-10-12T10:00:00+00:00"}
  ```
- Format rotacji (akceptowany rownolegle):
  ```json
  {"tokens": [{"token": "<hex1>", "created": "..."}, {"token": "<hex2>", "created": "..."}]}
  ```
- Loader `load_car_tokens()` (linia 788): `utf-8-sig` (BOM z PowerShell `Out-File`), min. 16 znakow, wynik to `set[str]`. Brak pliku / zly JSON / krotki token → `set()` → **401 na wszystko**.
- Naglowek: `Authorization: Bearer <token>`. Brak prefiksu `bearer ` → `401 {"error": "no bearer token"}`; prefiks z zlym tokenem → `401 {"error": "bad token"}`.
- Token sam w sobie — zadnej rotacji automatycznej na PoC (patrz `openspec/changes/carplay-okna-projektow/design.md` R10).

---

## Rejestr sesji CarPlay

- Plik: `~/.claude/carplay_sessions.json` (na pececie z bramka).
- Schemat per `session_id`:
  ```json
  {"<session_id>": {"project": "<resolved_name>", "ts": 1760000000, "state": "active"}}
  ```
- TTL: **600 s** (`CAR_SESSION_TTL_S`, linia 776). `car_get_active()` zwraca `None` gdy `now - ts > ttl_s`.
- `session_id` dostarcza HA (= `conversation_id` HA Assist); klucz jest nieprzezroczysty dla bramki, max 120 znakow.
- Ustawiane w `_car_dispatch` po poprawnym resolve (`car_set_active`) oraz w gale `set_only` (sama nazwa projektu bez promptu).
- Kasowane wprost przez `POST /api/car/zamknij` (uzytkownik mowi „zamknij" / „kończymy projekt").
- Zapis atomowy: `tmp + os.replace()` (bezpieczne na Windows).

---

## Odmowy (CAR_REFUSE_PATTERNS)

Linia 782, matching **po `.lower()` i normalizacji spacji**, pierwszy pasujacy wzorzec → odmowa, bez wolania Claude:

```
"git push", "git reset --hard", "rm -rf", "sudo ", "--force",
"--dangerously-skip-permissions", "drop table", "shutdown", "reboot", "format "
```

- Log: dopisywany do `project_integration/project_files/run_files/carplay_refusals.jsonl` jedna linia JSON per odmowa (`ts, session_id, project, prompt, pattern`).
- Odpowiedz: `200 {"text": "w aucie tego nie zrobie, zrob z telefonu", "outcome": "refused"}`.
- Celowo **nie** zastepuje ochron po stronie Claude — to dodatkowe sito wczesnego odrzucenia (nie dociera do tmux).

---

## Rozwiazywanie nazw projektow (`okna.resolve`)

Modul: `project_integration/tools/okna.py` linia 77. Zrodlo listy: `~/.claude/monitor_repos.env` (`REPOS_ENV`, linia 38).

Normalizacja: `re.sub(r"[^a-z0-9]", "", s.lower())` — ignoruje case, podkreslniki, mysniki, spacje.

Cztery warstwy, **pierwsza niepusta wygrywa** (dokladna nazwa nigdy nie przegrywa z dluzsza):

1. **exact**: `_norm(name) == _norm(query)`.
2. **prefix**: `_norm(name).startswith(_norm(query))`.
3. **substring**: `_norm(query) in _norm(name)`.
4. **token-match (≥ 2 slow)**: wszystkie tokeny zapytania obecne w `_norm(name)` niezaleznie od kolejnosci (np. `"car integration"` → `Car_chatGPT_integration`); dla 1-tokenowego zapytania juz obsluzone warstwa 3.

Wynik: `list[str]`. `0` kandydatow → `outcome: missing`; `>= 2` → `outcome: ambiguous` z Glosowo w stylu `"ktory projekt - A czy B"`.

W `_car_dispatch` dodatkowo `parse_car_prompt` (linia 823) probuje prefiksow 3-, 2-, 1-slowowych zanim spadnie do aktywnej sesji; obsluguje tez slowa kluczowe `kontynuuj` / `dalej` (mode=`continue`) i same nazwe bez reszty (mode=`set_only`).

---

## 1. POST /api/car/dispatch — glowny dispatcher

**Co robi**: parsuje prompt z HA Assist, rozwiazuje nazwe projektu (jawne pole, prefiks promptu albo sticky sesja), wysyla `[glos] <prompt>` do tmux okna projektu i czeka na pierwsza linie `Glosowo:` z panelu.

- Metoda: `POST`
- URL: `/api/car/dispatch`
- Naglowki: `Authorization: Bearer <token>`, `Content-Type: application/json`
- Body (JSON):
  ```json
  {"session_id": "<ha-conv-id, 1..120 znakow>",
   "project": "<nazwa lub nazwa fuzzy, opcjonalne, 0..120>",
   "prompt": "<tresc polecenia, 1..4000>"}
  ```
  Limity: body <= 16 KiB (`_json_body(limit=16*1024)`). `session_id` i `prompt` wymagane; bez nich `400 {"error": "need session_id and prompt"}`.
- Odpowiedz (JSON, zawsze 200 na scenariusze biznesowe — HA czyta `outcome`):
  ```json
  {"text": "<linia do wymowienia przez HA>",
   "outcome": "sent|ambiguous|missing|refused|timeout|resolved",
   "resolved_project": "<nazwa, opcjonalne>"}
  ```
  Mapa `outcome`:
  - `sent` — dostarczono i zlapano pierwsza linie `Glosowo:`.
  - `resolved` — tryb `set_only`: ustawiono sticky projekt, nic nie wyslano do tmux.
  - `ambiguous` — >= 2 kandydatow z resolve.
  - `missing` — nie ma projektu / nie ma okna tmux / sesja wygasla.
  - `refused` — pasujacy `CAR_REFUSE_PATTERNS`.
  - `timeout` — `CAR_WAIT_TIMEOUT_S` (30 s) uplynal bez linii `Glosowo:`.
- Timeout: `CAR_WAIT_TIMEOUT_S` = `30 s` (env var), polling co `0.5 s`.
- Logi: `log("car-dispatch", ...)`; miss logowany do `carplay_misses.jsonl`.
- Fuzzy: tak — pole `project` **i** parser prefiksu promptu uzywaja `okna.resolve`.

Przyklad curla:
```powershell
curl.exe -sS -X POST "https://desktop-geih38c.taileb4004.ts.net:8788/api/car/dispatch" `
  -H "Authorization: Bearer $env:CAR_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{"session_id":"ha-conv-abc","project":"car integration","prompt":"co nowego w sesji"}'
```

---

## 2. GET /api/car/status — agregat wszystkich projektow

**Co robi**: ciagnie `/api/state` z Monitor (lokalny addon na pececie), skraca do Glosowo-friendly linii dla auta (ile projektow, ile pracuje, lacznie otwartych zadan, pierwszy aktywny).

- Metoda: `GET`
- URL: `/api/car/status`
- Naglowki: `Authorization: Bearer <token>`
- Body: brak
- Odpowiedz (JSON):
  ```json
  {"text": "<krotki Glosowo>",
   "outcome": "sent|timeout",
   "working": <int, liczba projektow w stanie `working`>,
   "tasks_open": <int, suma otwartych taskow>,
   "total_projects": <int>}
  ```
  `outcome: timeout` + `text: "monitor nie odpowiada"` przy padnietym Monitorze.
- Timeout: 5 s na wolanie Monitor API (`api(cfg, "GET", "/api/state", timeout=5.0)`).
- Fuzzy: n/d.
- Logi: `log("car-status", ...)`, obciete do 120 znakow.

Przyklad:
```powershell
curl.exe -sS "https://desktop-geih38c.taileb4004.ts.net:8788/api/car/status" `
  -H "Authorization: Bearer $env:CAR_TOKEN"
```

---

## 3. POST /api/car/open — otworz okno projektu

**Co robi**: resolve nazwy przez `okna.resolve`, delegacja do `tools/okno.py` (Windows Terminal + `tmux new-session -A`). Idempotentne: dla juz otwartego okna zwraca `aktywny` z Glosowo `"okno X juz dziala"`.

- Metoda: `POST`
- URL: `/api/car/open`
- Naglowki: `Authorization: Bearer <token>`, `Content-Type: application/json`
- Body: `{"project": "<nazwa lub fuzzy, 1..120>"}`
- Odpowiedz:
  ```json
  {"text": "otwieram <X> | okno <X> juz dziala",
   "outcome": "sent|ambiguous|missing",
   "resolved_project": "<nazwa>",
   "raw": "<surowy stdout okna.py>"}
  ```
- Timeout: `subprocess.run(..., timeout=45)` na okno.py (45 s — pierwsze otwarcie tmux + ask_core moze trwac).
- Fuzzy: tak (`okna.resolve`).
- Blad resolve: `500 {"error": "resolve failed"}`; blad okno.py: `500 {"error": "okno failed"}`.
- Logi: `log("car-open", ...)`.

Przyklad:
```powershell
curl.exe -sS -X POST "https://desktop-geih38c.taileb4004.ts.net:8788/api/car/open" `
  -H "Authorization: Bearer $env:CAR_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{"project":"ribnxtr"}'
```

---

## 4. GET /api/car/project/<name>/summary — podsumowanie projektu

**Co robi**: resolve fuzzy, odczyt rekordu projektu z `/api/state` Monitor, buduje Glosowo z aktualnym stanem (`state`, `done/total`, aktywny task).

- Metoda: `GET`
- URL: `/api/car/project/<name>/summary` (segment URL, URL-decoded po stronie bramki)
- Naglowki: `Authorization: Bearer <token>`
- Body: brak
- Odpowiedz:
  ```json
  {"text": "<Glosowo>",
   "outcome": "sent|ambiguous|missing|timeout",
   "resolved_project": "<nazwa>",
   "state": "<stan z Monitora>",
   "done": <int>,
   "total": <int>}
  ```
- Timeout: 5 s na wolanie Monitor API.
- Fuzzy: tak (`okna.resolve` na nazwie z URL).
- Logi: `log("car-project", ...)`.

Przyklad:
```powershell
curl.exe -sS "https://desktop-geih38c.taileb4004.ts.net:8788/api/car/project/car%20integration/summary" `
  -H "Authorization: Bearer $env:CAR_TOKEN"
```

---

## 5. POST /api/car/todo — zapis TODO

**Co robi**: dopisuje jedna linie JSON do `~/.claude/carplay_todos.jsonl`. Projekt bierze z body albo (gdy puste) z aktywnej sesji; probuje fuzzy resolve, ale **akceptuje nierozwiazane** (lepiej miec surowa nazwe niz nic).

- Metoda: `POST`
- URL: `/api/car/todo`
- Naglowki: `Authorization: Bearer <token>`, `Content-Type: application/json`
- Body:
  ```json
  {"text": "<tresc TODO, 1..500>",
   "project": "<opcjonalne, 0..120>",
   "session_id": "<opcjonalne, 0..120 — do fallbacku na sticky>"}
  ```
- Odpowiedz:
  ```json
  {"text": "zapisane do <X> | zapisane bez projektu",
   "outcome": "sent",
   "resolved_project": "<X lub null>",
   "iso": "2026-10-12T10:00:00+00:00"}
  ```
- Zapis: `~/.claude/carplay_todos.jsonl`, append, `utf-8`.
- Timeout: n/d (synchroniczny zapis pliku).
- Fuzzy: tak (`okna.resolve`), ale **nie wymaga** jednoznacznego trafienia.
- Blad: `500 {"error": "save failed"}` tylko na blad OSError na pliku.
- Logi: `log("car-todo", ...)`.

Przyklad:
```powershell
curl.exe -sS -X POST "https://desktop-geih38c.taileb4004.ts.net:8788/api/car/todo" `
  -H "Authorization: Bearer $env:CAR_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{"text":"sprawdzic skrypt pomiarowy","project":"car","session_id":"ha-conv-abc"}'
```

---

## 6. POST /api/car/zamknij — jawne zamkniecie sticky

**Co robi**: usuwa wpis `session_id` z `~/.claude/carplay_sessions.json`. Uzyteczne gdy uzytkownik chce przełączyc projekt bez czekania na TTL 600 s.

- Metoda: `POST`
- URL: `/api/car/zamknij`
- Naglowki: `Authorization: Bearer <token>`, `Content-Type: application/json`
- Body: `{"session_id": "<ha-conv-id, 1..120>"}`
- Odpowiedz:
  ```json
  {"text": "zamkniete, bylo <projekt> | nie bylo aktywnej sesji",
   "outcome": "sent",
   "previous_project": "<nazwa lub null>"}
  ```
- Timeout: n/d.
- Fuzzy: n/d.
- Logi: `log("car-zamknij", ...)`.

---

## 7. GET /api/car/test-audio — diagnostyka audio

**Co robi**: diagnostyczny endpoint PoC (**bez tokenu**, bind na tailnet). Zwraca `audio/mpeg` z nagranym `"test glosu w aucie"` przez `speak()` (ten sam wybor glosu co w HA / PI: VCC warm → HA proxy → edge-tts).

- Metoda: `GET`
- URL: `/api/car/test-audio`
- Naglowki: brak
- Body: brak
- Odpowiedz: `200 audio/mpeg` (binarny `audio.mp3` z `speak(CAR_TEST_TEXT)`).
- Timeout: n/d (synchroniczny `speak()`).
- Logi: `log("car-poc", "test-audio HIT ua=... remote=...")` i `"test-audio OK dt=%.2f"` po zwrocie.
- Usuniecie: zaplanowane po pomiarze (`openspec/changes/carplay-okna-projektow` task 7.1).

---

## 8. GET /api/car/test-text — diagnostyka tekst

**Co robi**: wariant tekstowy porownawczy z `/api/car/test-audio`. Oddaje `"test glosu w aucie"` jako `text/plain`, by Shortcut iOS mogl odtworzyc przez Speak Text (wlasna sesja Siri, czesto dociaga do konca gdy Play Sound jest ucinany przez CarPlay).

- Metoda: `GET`
- URL: `/api/car/test-text`
- Naglowki: brak
- Body: brak
- Odpowiedz: `200 text/plain; charset=utf-8` body = `CAR_TEST_TEXT`.
- Timeout: n/d.
- Logi: `log("car-poc", "test-text HIT ua=... remote=...")`.
- Usuniecie: razem z `/api/car/test-audio`, task 7.1.

---

## Jak HA to wola — wzorzec `rest_command`

Nagrywany w `voice/rest_command_claude.yaml` po stronie HA (Pi). Analogia do `pm_zapytaj` z addona Monitor (`addons/project_monitor/ha/project_monitor_pytania.yaml`, linia 28). Przyklad dla **dispatcher**:

```yaml
rest_command:
  claude_dispatch:
    url: !secret car_dispatch_url   # https://desktop-geih38c.taileb4004.ts.net:8788/api/car/dispatch
    method: POST
    headers:
      Authorization: !secret car_token   # "Bearer 0123456789abcdef..."
      Content-Type: "application/json"
    # to_json jest kluczowe: apostrofy / cudzyslowy / polskie znaki w promptcie bez niego
    # rozwala JSON (patrz pm_zapytaj).
    payload: >-
      {"session_id": {{ conversation.id | to_json }},
       "project":    {{ project | default('')  | to_json }},
       "prompt":     {{ prompt  | to_json }}}
```

Potem w `voice/claude_sentences_pl.yaml` sentence pattern (`"Claude, do okna {project}, {prompt}"` / `"Claude, {prompt}"`) odpala intent, ktory wola `rest_command.claude_dispatch`, a odpowiedz (`text`) wraca do HA Assist jako tekst do TTS (Piper / VCC proxy).

Dla `/api/car/open`, `/api/car/todo`, `/api/car/zamknij` analogiczna definicja, inne body. Dla `GET /api/car/status` i `/project/<name>/summary` **sensor REST** w HA (jak `PM ostatnia odpowiedz`) albo rest_command z `method: GET`.

---

## Pliki referencyjne

- Kod: `D:\claude_projekty\project_integration\tools\voice_gateway.py` (sekcja Car linie 760-2240, `_car_*` 1814-2240)
- Resolver: `D:\claude_projekty\project_integration\tools\okna.py` (`resolve` linia 77, `parse_repos` linia 59, `REPOS_ENV` linia 38)
- Mostek do tmux: `D:\claude_projekty\project_integration\tools\cli_bridge.py` (`tmux_name`, `capture`, `type_into`, `extract_reply`, `spoken_lines`, `VOICE_TAG`)
- Design + plan: `D:\claude_projekty\Car_chatGPT_integration\openspec\changes\carplay-okna-projektow\design.md`
- Spec kontraktu: `D:\claude_projekty\Car_chatGPT_integration\openspec\changes\carplay-okna-projektow\specs\car-window-dispatch\spec.md`
- Siostrzany HANDOFF: `D:\claude_projekty\Car_chatGPT_integration\notes\HANDOFF_carplay_okna.md`
- Konfig HA (szablon): `D:\claude_projekty\project_integration\addons\project_monitor\ha\project_monitor_pytania.yaml`

---

## Operacyjne pulapki

- **BOM w `car_tokens.json`**: `Out-File -Encoding utf8` z Win PS 5.1 pisze UTF-8-BOM; loader obsluguje przez `utf-8-sig`. **Nie uzywac `utf-16`**.
- **Pusty `monitor_repos.env`**: `resolve` zwroci `[]` → kazda dispatch koncy sie `outcome: missing`. Zweryfikuj przez `tools/ready.py --apply` na nowej maszynie.
- **Monitor pada**: `/api/car/status` i `/project/<name>/summary` zwracaja `outcome: timeout` z tekstem `"monitor nie odpowiada"`. HA powinien na ten `outcome` zareagowac innym komunikatem niz `sent`.
- **Timeout 30 s w dispatch**: dluga odpowiedz Claude przekracza `CAR_WAIT_TIMEOUT_S` → `outcome: timeout` + Glosowo `"pracuje jeszcze, zapytaj za chwile"`. Prompt **i tak dotarl do tmux** — kolejne wywolanie moze przejsc `kontynuuj` i zlapac wynik.
- **Sticky TTL 600 s**: po 10 min bez `dispatch` sesja znika; nastepne `dispatch` bez pola `project` zwroci `"sesja wygasla, powiedz do okna X"`.
