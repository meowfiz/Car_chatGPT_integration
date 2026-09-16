# `ask_server.py` jako klient wspólnego rdzenia `ask_core`

## Why

Ten projekt i `project_integration` zbudowały niezależnie ten sam mechanizm: „zadaj pytanie
o stan repozytoriów, odpowiedz z `claude -p` tylko do odczytu". Tutaj wejściem jest głos w aucie
(`poc/ask_server.py`: Whisper → `ask_claude` → mowa), tam telefon i Home Assistant
(`monitor/ask_worker.py`: skrzynka w dodatku → `claude -p` → powiadomienie).

Porównanie **kodu** obu stron, 2026-09-16 (nie opisów):

| | `poc/ask_server.py` (tu) | `monitor/ask_worker.py` (monitor) |
|---|---|---|
| zakres | wszystkie repo w jednym wywołaniu (`--add-dir`) | jedno repo albo `*` = wszystkie (od dziś) |
| świeżość | `sync_repo`: `pull --ff-only` tylko przy czystym drzewie, wiek mówiony głośno | **brak** |
| ochrona | `--allowedTools` **i** `--disallowedTools`, `--append-system-prompt`, `--model` | `--allowed-tools`, system prompt |
| mapa repo | `ASK_REPOS` / skan `ASK_ROOT` | `~/.claude/monitor_repos.env`, uzupełnia się sama z `session_start` |
| rezydent | serwer HTTP + Harmonogram Windows + watchdog (`poc/deploy/`) | worker z pierwszego okna Claude Code; po restarcie kompa luka |
| wyjście | `for_speech` (mowa, ≤ 700 znaków) | tekst, powiadomienie, encja HA |

Decyzja użytkownika 2026-09-16: **jeden wspólny rdzeń, dwa projekty**. Kanon zmiany leży
w `project_integration/openspec/changes/ask-core/`; tutaj są zadania klienta.

Dodatkowy argument z tego samego dnia: w monitorze **żadne pytanie nie docierało do modelu** —
`shutil.which("claude")` zwraca `claude.CMD`, a cmd.exe ucina argument na pierwszym znaku nowej
linii, więc prompt `instrukcja\n\nPytanie: ...` gubił pytanie; model streszczał repo i wyglądało to
jak odpowiedź. Ten projekt uniknął tego przypadkiem (`shell=True`, prompt bez nowej linii
w argumencie, pytanie osobno). Jedna implementacja `claude -p` = jedno miejsce, w którym taki błąd
może istnieć, i jeden test, który go łapie.

## What changes

1. `poc/ask_server.py` przestaje mieć własne `ask_claude` i `for_speech`; woła
   `ask_core.ask(...)` i `ask_core.for_speech(...)` z paczki (`monitor/ask_core.py`, instalowanej
   przez `install_pack.py` w każdym repo). Wywołanie zostaje **synchroniczne** — kolejka monitora
   dodałaby do 30 s pollingu, a tu celem jest 15 s.
2. `sync_repo` / `sync_all` przenoszą się **do rdzenia** jako `refresh_repo` — to jest wkład tego
   projektu, dziś najlepsza część obu implementacji.
3. Mapa repo: domyślnie `~/.claude/monitor_repos.env` (ta sama, którą uzupełnia hook
   `session_start` w każdym repo); `ASK_REPOS` / `ASK_ROOT` zostają jako jawne nadpisanie.
4. `poc/deploy/02_install_tasks.ps1` instaluje dodatkowo `monitor/ask_worker.py --spawn` przy
   logowaniu — jeden rezydent więcej kosztuje nic, a domyka lukę monitora „worker rusza dopiero
   z pierwszym oknem Claude Code" (`remote-tasks` 2.7).
5. `SYSTEM` (prompt kierowcy: trzy zdania, bez markdown, bez ścieżek) zostaje **tutaj** i jest
   podawany do rdzenia jako parametr — to jest różnica produktowa, nie techniczna.

## Czego to NIE zmienia

- Ścieżka głosowa: skrót na iPhonie, Whisper, HTTP na pececie, `for_speech` — bez zmian.
- Zadania zapisujące z głosu: nadal poza zakresem (bramki reguł 2.7–2.9).
- Pomiary: po przejściu na rdzeń trzeba **powtórzyć** 2.7 (czas odpowiedzi), bo zmienia się
  sposób wywołania `claude`.
