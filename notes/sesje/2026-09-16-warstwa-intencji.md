# Sesja 2026-09-16 (sesja 3: warstwa intencji mostu głosowego)

Zadanie z `notes/prompty/2026-09-16-most-glosowy.md`. Repo na starcie czyste i zgodne z `origin/main`
(`5a0fbbc`).

## Co zrobiono

**Zmiana OpenSpec `voice-intent`** (proposal + design + spec + 29 zadań), `openspec validate
--strict` zielony — napisana **przed** kodem.

**Schemat intencji v1**: `{v, intent, repo, repo_reason, text, limit_zdan}`. Zaimplementowany
wyłącznie `intent: ask`; `note` i `queue` są rozpoznawane i **odrzucane zdaniem po polsku
z kodem HTTP 200** (skrót na iPhonie czyta treść odpowiedzi — kod błędu skończyłby się ciszą).

**Nowe pliki**
- `poc/aliases.json` — tablica aliasów jako **dane**: klucz = nazwa kanoniczna repo, wartość =
  formy mówione („carcha gpt", „ribnikster", „jot ka", „hom asystent"). Dodanie projektu to jeden
  wpis, zero zmian w kodzie. Nazwy kanoniczne sprawdzane wobec `~/.claude/monitor_repos.env`.
- `poc/intent.py` — parser deterministyczny (same funkcje czyste, tylko stdlib): normalizacja
  (polskie znaki → ASCII), dopasowanie aliasu po n-gramach słów przez `difflib`, próg `min_ratio`
  z pliku danych, limit zdań z frazy, słowa kluczowe intencji.
- `project_files/python/tests/fixtures/wypowiedzi.json` — 43 wypowiedzi, każda z polem `zrodlo`
  (`log` = prawdziwa transkrypcja Whispera, `syntetyczna` = pisana przy biurku).
- `project_files/python/intent_accuracy.py`, `project_files/python/intent_scope_time.py` — dwa
  przebiegi pomiarowe z nagłówkiem proweniencji (commit, czystość drzewa, SHA-256 wejść).
- `project_files/python/tests/test_intent.py` — 18 testów.

**Zmiany w `poc/ask_server.py`**: `intent.parse()` po transkrypcji przed `ask_claude`; odmowa dla
`note`/`queue`; `repos_for()` zawężające zakres do jednego katalogu, gdy repo rozpoznane (z powrotem
do wszystkich, gdy ta maszyna takiego repo nie ma); instrukcja zakresu doklejana do promptu; log
i `?format=json` niosą `intent`, `repo` i **powód** dopasowania.

## Kluczowe decyzje / zmiany semantyki

- **Rozwidlenie z promptu rozstrzygnięte na (a)**: gdy reguły nie rozpoznają repo, pytamy wszystkie
  przez `--add-dir`, bez dopytywania głosem. Dlaczego: kosztuje zero sekund, jest zgodne z „nazwij
  repo w odpowiedzi", a przy błędnym parserze najgorszy skutek to dzisiejszy czas odpowiedzi, a nie
  odpowiedź o cudzym projekcie. Konsekwencja: `*` znaczy dwie rzeczy, więc log **musi** rozróżniać
  `explicit-all` od `no-match` — inaczej pomiar trafności nie ma czego liczyć.
- **Rezerwa modelowa świadomie pominięta** (prompt ją dopuszczał). W zakresie `ask` obie
  niepewności mają tani wynik domyślny (`ask` i `*`), więc drugie wywołanie LLM kosztowałoby
  sekundy za rzecz, która i tak działa. Wraca jako pytanie dopiero z `note`/`queue`, gdzie zła
  intencja **zapisuje** nie tam. Zapisane w `design.md`, żeby nie odkrywać tego drugi raz.
- **Aliasy krótsze niż 4 znaki dopasowują się tylko jako całe słowa**, nigdy rozmyto — inaczej „dom"
  (alias HA) łapie „do domu". To reguła w kodzie z własnym testem.
- **`limit_zdan` tylko z liczby wypowiedzianej wprost.** „Krótko" nie jest liczbą; domyślne trzy
  zdania są już w prompcie kierowcy, a zgadywanie liczby z przysłówka wymyśla decyzję, której nikt
  nie podjął.

## Liczby

**PREREJESTRACJA 5.1 (trafność rozpoznania repo) — zapisana przed przebiegiem, wynik POZYTYWNY.**
Fixture 43 wypowiedzi, 31 z nazwanym projektem.

| | liczba |
|---|---|
| trafienia | 26 / 31 = **83,9%** (hipoteza ≥ 80%, negatyw < 70%) |
| fałszywe trafienia | 1 / 43 = **2,3%** (warunek bezpieczeństwa ≤ 10%) |
| przeoczenia (uczciwe `*`) | 4 |
| uczciwe `*` tam, gdzie `*` było oczekiwane | 12 / 12 |
| rozbicie `zrodlo` | `log` 2/2 trafione; `syntetyczna` 24/29 |

Próg `min_ratio` = 0,82 zadeklarowany z góry, **1 testowane porównanie**, nie strojony po wyniku.

**Wynik nie uprawnia** do zdania o mowie w jadącym aucie: 41 z 43 wypowiedzi napisano przy biurku,
a fixture pisany przy biurku jest łatwiejszy niż nagranie z szosy. Liczba z prawdziwych nagrań może
być tylko gorsza — dlatego zadanie 5.6 (nagrać ≥ 10 prawdziwych) zostaje otwarte.

**Dwa słabe aliasy zmierzone, świadomie NIEPOPRAWIONE w tej sesji.** Jedyne fałszywe trafienie:
alias `projekt car` złapał „**który projekt** ma najwięcej otwartych zadań". Jedno przeoczenie tego
samego rodzaju: `kazdy projekt` (lista „wszystkie") złapał „**czy projekt** integracji projektów…".
Usunięcie ich teraz, po zobaczeniu wyników, byłoby strojeniem do fixture (ZASADY 5.4) — stąd zadanie
5.5: najpierw dopisać ≥ 10 nowych wypowiedzi, potem zmienić aliasy, potem przemierzyć i zapisać
obie liczby jako **drugie**, jawnie policzone porównanie.

**PREREJESTRACJA 5.2 (czy zawężenie zakresu skraca odpowiedź).** WYNIK_5_2

## Testy

25 testów zielonych (7 dotychczasowych + 18 nowych). **Sprawdzenie mutacją (ZASADY 4.4)** — sześć
mutacji, każda złapana, po przywróceniu 25/25:

| mutacja | padło testów |
|---|---|
| `normalize` bez tablicy polskich znaków | 2 |
| `MIN_FUZZY_LEN = 1` (krótkie aliasy rozmyte) | 1 |
| `parse_intent` zawsze zwraca `ask` | 3 |
| `parse_limit` zgaduje 2 przy braku liczby | 1 |
| `repos_for` nie zawęża zakresu | 1 |
| odmowa `note` wysyłana z kodem 400 zamiast 200 | 1 |

## Moje błędy w tej sesji (ZASADY 1.3)

- **Zaznaczyłem zadania jako `[x]` w `tasks.md` zanim je zrobiłem** (pisząc plik z góry). Wyszło
  bez szkody, bo wszystkie zostały wykonane w tej samej sesji, ale to jest dokładnie ten nawyk,
  który robi z `STATUS.md` fikcję. Następnym razem: `[ ]` przy tworzeniu, `[x]` po przebiegu.
- **Pierwsza wersja sprawdzania „wszystkie projekty" wymagała dopasowania dokładnego** (`>= 1.0`),
  więc „wszystkich projektach" wpadłoby w `no-match`. Złapane w smoke teście przed napisaniem
  testów, naprawione progiem `min_ratio`.
- Pomiar 5.2 puściłem w tle przez `| tail`, co zbuforowało całe wyjście — przez kilka minut nie
  było widać, czy liczy, czy zawisło. To jest ZASADA 4.6 (postęp) obejście własnym potokiem.

## Aktywne TODO / pending

- `voice-intent` 5.4 (przebieg pomiaru czasu), 5.5 (słabe aliasy + drugi pomiar), 5.6 (prawdziwe
  nagrania do fixture), 6.3 (akapit w `HANDOFF_most_pytan.md`).
- Bez zmian: `poc-carplay-command` 1.6–1.9 (wdrożenie na pececie w pracy), 2.7 (czas odpowiedzi);
  `ask-core-client` czeka na `monitor/ask_core.py` z `project_integration`.

## Pliki zmienione

- `openspec/changes/voice-intent/{proposal,design,tasks}.md`, `specs/voice-intent/spec.md`,
  `.openspec.yaml` — nowa zmiana (opis powyżej).
- `openspec/STATUS.md` — wygenerowany `notes/gen_openspec_status.py`.
- `poc/intent.py` (nowy) — parser intencji, same funkcje czyste.
- `poc/aliases.json` (nowy) — aliasy repozytoriów jako dane.
- `poc/ask_server.py` — wpięcie parsera, odmowa zapisu, zawężenie zakresu, log z powodem
  dopasowania; `ask_claude` przyjmuje katalogi i dodatkowy system prompt.
- `project_files/python/tests/test_intent.py` (nowy) — 18 testów nazywających porażki.
- `project_files/python/tests/fixtures/wypowiedzi.json` (nowy) — fixture z polem `zrodlo`.
- `project_files/python/intent_accuracy.py` (nowy) — przebieg prerejestracji 5.1.
- `project_files/python/intent_scope_time.py` (nowy) — przebieg prerejestracji 5.2.
- `notes/sesje/2026-09-16-warstwa-intencji.md` (ten plik), `notes/start.md`.
