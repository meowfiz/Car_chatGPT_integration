# Prompt do odpalenia w sesji Car: most głosowy → język naszych mechanizmów

Przygotowany 2026-09-16 przez sesję `project_integration`. Do wklejenia w Claude Code w repo
`Car_chatGPT_integration` w dowolnym momencie — **ta praca nie zależy od `ask_core`**, warstwa
intencji stoi przed nim.

---

## PROMPT (do skopiowania od tej linii)

Zbuduj warstwę intencji dla mostu głosowego: zamień swobodną polską mowę kierowcy na **strukturę,
którą rozumieją nasze mechanizmy**. Dziś `poc/ask_server.py` przekazuje surową transkrypcję prosto
do `claude -p` — działa dla pytań, ale nie odróżnia „zapytaj" od „zanotuj" i nie wie, o które
repozytorium chodzi, dopóki model sam się nie domyśli z plików.

Zacznij od zmiany OpenSpec `voice-intent` (proposal, design, tasks) — nie od kodu.

### Co już jest zmierzone (nie mierz tego ponownie)

- Transkrypcja Whisperem: **2,1 s**. Pełna pętla: **13,8–34,5 s**. Wąskie gardło to Claude czytający
  pliki, **nie głos** — próg 15 s z zadania 2.7 nie jest nietrafiony przez transkrypcję.
- `sync_all` czterech repo: 1,95 s.
- Po stronie monitora (2026-09-16): pytanie z HA → odpowiedź w 24–36 s; zakres „wszystkie projekty"
  przez `--add-dir` działa i odpowiada na pytania porównawcze („który projekt ma najwięcej otwartych
  zadań" → RibnXtr2026, 275).
- Mapa repo tej maszyny: `~/.claude/monitor_repos.env` (`NazwaRepo=ścieżka`), uzupełnia się sama —
  każde repo otwarte w Claude Code dopisuje się przy `session_start`.
- Skrzynka monitora: `POST /api/inbox` `{repo, kind, text}`, `kind: "ask"` działa, `kind: "task"`
  jest celowo odrzucany (422) do czasu bramek reguł 2.7–2.9.

### Co zbudować

**1. Schemat intencji** — mały, wersjonowany, opisany w `design.md`. Propozycja wyjściowa:

```
{"v": 1, "intent": "ask" | "note" | "queue", "repo": "<nazwa> | * | null",
 "text": "<treść>", "limit_zdan": <int|null>}
```

`ask` → pytanie (dziś), `note` → dopisanie do notatek, `queue` → odłożenie zamiaru w skrzynce.
Zaimplementuj **teraz tylko `ask`**; pozostałe dwa opisz w schemacie i odrzucaj z jasnym komunikatem
głosowym („zapisywanie notatek jeszcze nie działa"). Powód: każdy zapis wymaga bramek, których nie ma.

**2. Rozpoznanie repozytorium z mowy.** To jest sedno. Mówisz „projekt JK", „ribnikster", „monitor",
„auto" — Whisper przekręci każdą z tych nazw. Potrzebna **tablica aliasów jako dane, nie kod**
(np. `poc/aliases.json`), żeby dodanie projektu nie wymagało zmiany kodu, plus dopasowanie odporne
na literówki. Nazwy kanoniczne bierz z `~/.claude/monitor_repos.env`, żeby nie powstała druga lista.

**3. Parser deterministyczny przed modelem.** Najpierw reguły (słowa kluczowe + aliasy + limit zdań
z frazy „w dwóch zdaniach"), a model dopiero jako **rezerwa**, gdy reguły nie rozstrzygną. Powód:
drugie wywołanie LLM to kolejne sekundy, a cel to 15 s.

**4. Ścieżka powrotna.** Format odpowiedzi zależy od intencji; `for_speech` zostaje.

### Decyzje już podjęte (nie relitygować)

- **Siri nie jest odpowiedzią na czas.** Dyktowanie Siri zamiast Whispera oszczędza ~2 s przy wąskim
  gardle 13–34 s. Sens Siri to **wyzwalanie bez rąk** („Hej Siri, zapytaj projekt…"), nie prędkość.
  Jeśli robisz skrót Siri, rób go dla wygody, i nie licz na tym zysku czasowego.
- **Zamiast pytania potwierdzającego — nazwij repo w odpowiedzi.** „Czy chodzi o RibnXtr?" podwaja
  czas pętli. Odpowiedź zaczynająca się od „W RibnXtr…" daje tę samą informację za darmo: usłyszysz
  złe trafienie od razu. Potwierdzenie zostaw wyłącznie dla `note` i `queue`, gdy powstaną.
- **Wywołanie zostaje synchroniczne** (skrzynka monitora dodałaby do 30 s pollingu).
- **Zapis (`note`, `queue`) poza zakresem tej zmiany.**

### Rozwidlenie do rozstrzygnięcia przez Ciebie

Gdy reguły nie rozpoznają repozytorium: (a) zapytać wszystkie przez `--add-dir` i pozwolić modelowi
wybrać, czy (b) dopytać głosem. Moja rekomendacja: **(a)**, bo kosztuje zero dodatkowych sekund
i jest zgodne z „nazwij repo w odpowiedzi". Ale to Twoja decyzja — zapisz ją w `design.md` z „dlaczego".

### Jak pracować

- Reguły z `ZASADY_PRACY.md`: zmiana OpenSpec przed kodem, testy **nazywające porażkę** i sprawdzone
  mutacją, ASCII w kodzie i komentarzach, notatka sesji przed commitem.
- **PREREJESTRACJA** (reguła 3.3) dla pomiaru trafności parsera: ile wypowiedzi, jak liczysz trafienie
  repozytorium, jaki warunek negatywu. Bez tego nie raportuj „działa dobrze".
- Fixture z **prawdziwych** transkrypcji, łącznie z przekręconymi nazwami — parser, który działa
  tylko na poprawnie wymówionych nazwach, nie rozwiązuje problemu, który ma rozwiązać.
- Nie ruszaj `monitor/*.py` — to pliki paczki, kanon jest w `project_integration`.

### Kontekst, którego możesz nie mieć

Trwa równoległa zmiana `ask-core` (`project_integration`): wspólny rdzeń „zapytaj repo" dla mostu
głosowego i dla Home Assistanta, bo oba projekty zbudowały to samo. Twoja zmiana `ask-core-client`
czeka na `monitor/ask_core.py`. **Warstwa intencji jest od tego niezależna** — po powstaniu rdzenia
podasz mu gotową strukturę zamiast surowego tekstu.

Jedna rzecz stamtąd warta zapamiętania: w monitorze przez pół dnia **żadne pytanie nie docierało do
modelu**, bo `shutil.which("claude")` daje `claude.CMD`, a cmd.exe ucina argument na pierwszym znaku
nowej linii — odpowiedzi wyglądały sensownie, bo model streszczał repo. Ty uniknąłeś tego przypadkiem
(`shell=True`). Gdy będziesz budował wywołania, trzymaj pytanie poza argv.
