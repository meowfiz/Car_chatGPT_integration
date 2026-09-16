# Warstwa intencji: mowa kierowcy -> struktura, ktora rozumieja nasze mechanizmy

## Why

Dzis `poc/ask_server.py` bierze surowa transkrypcje Whispera i wklada ja prosto do `claude -p`.
To dziala dla pytan, ale ma trzy konsekwencje:

1. **Most nie odroznia zamiaru.** „Zapytaj, ile zadan zostalo" i „zanotuj, ze trzeba dokonczyc
   watchdoga" ida ta sama sciezka; drugie zdanie model potraktuje jako pytanie i odpowie na nie
   zamiast cokolwiek zapisac. Kierowca nie uslyszy, ze zapis nie istnieje.
2. **Most nie wie, o ktore repozytorium chodzi**, dopoki model sam sie nie domysli z plikow.
   To jest dokladnie ta czesc petli, ktora kosztuje najwiecej: zmierzone 13,8-34,5 s, a waskim
   gardlem jest Claude czytajacy pliki, nie glos (transkrypcja 2,1 s).
3. **Nazwy projektow wracaja z Whispera przekrecone.** Jedyna prawdziwa transkrypcja audio, jaka
   mamy w logu (2026-09-14, dwa przebiegi), brzmi: „Ile zadan zostalo w projekcie **Carcha gpt
   integration** i co jest nastepne." Nazwa kanoniczna to `Car_chatGPT_integration`. Dopasowanie
   dokladne nie ma tu czego dopasowac.

## What changes

1. **Schemat intencji** w wersji 1, opisany w `design.md` i w specyfikacji:
   `{"v": 1, "intent": "ask" | "note" | "queue", "repo": "<nazwa>" | "*" | null,
   "text": "...", "limit_zdan": <int|null>}`.
2. **Implementowany jest wylacznie `intent: ask`.** `note` i `queue` sa w schemacie, sa
   rozpoznawane i sa **odrzucane** zdaniem do przeczytania glosem („Zapisywanie notatek jeszcze
   nie dziala"). Powod: kazdy zapis wymaga bramek z regul 2.7-2.9, ktorych tu nie ma.
3. **Tablica aliasow repozytoriow jako dane** (`poc/aliases.json`), nie kod: nowy projekt =
   jeden wpis w JSON, zero zmian w kodzie. Nazwy kanoniczne pochodza z
   `~/.claude/monitor_repos.env` — zeby nie powstala druga lista repozytoriow.
4. **Parser deterministyczny** (`poc/intent.py`): slowa kluczowe intencji, dopasowanie aliasow
   odporne na literowki (`difflib`, tylko stdlib), limit zdan z frazy „w dwoch zdaniach".
   Zero dodatkowych wywolan modelu — patrz `design.md`, sekcja „Rezerwa modelowa".
5. **Rozpoznane repozytorium zaweza zakres pytania**: `claude -p` dostaje wtedy jeden katalog
   zamiast wszystkich przez `--add-dir`. To jest jedyny mierzalny zysk czasowy tej zmiany
   i dlatego ma wlasna prerejestracje (zadanie 5.2), a nie zdanie „powinno byc szybciej".
6. **Sciezka powrotna nazywa repozytorium** zamiast pytac o potwierdzenie: odpowiedz zaczyna sie
   od nazwy repo, wiec zle trafienie slychac od razu i za darmo.

## Czego to NIE zmienia

- **Zapis (`note`, `queue`) pozostaje poza zakresem.** Rozpoznanie tak, wykonanie nie.
- **Wywolanie zostaje synchroniczne** — skrzynka monitora dodalaby do 30 s pollingu, a cel to 15 s.
- **Whisper zostaje.** Dyktowanie Siri oszczedza ~2 s przy waskim gardle 13-34 s; sens Siri to
  wyzwalanie bez rak, nie predkosc.
- **`SYSTEM` (prompt kierowcy)** zostaje w tym repo i jest tylko uzupelniany o zdanie o zakresie.
- **Nie zalezy od `ask_core`** (`ask-core-client`). Warstwa intencji stoi przed rdzeniem: po jego
  powstaniu poda mu gotowa strukture zamiast surowego tekstu, a `poc/intent.py` sie nie zmieni.
- **Nie rusza `monitor/*.py`** — to pliki paczki, kanon jest w `project_integration`.

## Warunek negatywu calej zmiany

Jesli na fixturze wypowiedzi (zadanie 5.1) trafnosc repozytorium wyjdzie ponizej **70%** przy
akceptowalnym progu, albo odsetek **falszywych trafien** (wskazane repo != oczekiwane, zamiast
uczciwego `*`) przekroczy **10%**, to reguly nie rozwiazuja problemu, ktory mialy rozwiazac.
Wtedy: `repo` zostaje na stale `*` (dzisiejsze zachowanie, zero regresu), a rozwidlenie wraca
jako pytanie o rezerwe modelowa — z pomiarem, ile sekund kosztuje.
