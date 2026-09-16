# Design: warstwa intencji mostu glosowego

## Gdzie to siedzi

```
skrot iPhone --audio--> ask_server.py
                           |
                           +-- transcribe()          Whisper, 2,1 s (bez zmian)
                           +-- intent.parse(text) <<< NOWE: tekst -> struktura
                           |      |
                           |      +-- intent: ask   -> pytanie z zawezonym zakresem
                           |      +-- note / queue  -> odmowa glosem, koniec
                           |
                           +-- ask_claude(question, repos)   zakres z intencji
                           +-- for_speech()                  bez zmian
```

Parser jest **czysta funkcja** (`ZASADY 4.5`): wejscie tekst + tablica aliasow, wyjscie slownik.
Nie czyta sieci, nie czyta zegara, nie wola modelu. Dzieki temu caly pomiar trafnosci (zadanie 5.1)
to jedna petla po fixturze, bez uruchamiania serwera.

## Schemat intencji, wersja 1

```
{"v": 1,
 "intent": "ask" | "note" | "queue",
 "repo":  "<nazwa kanoniczna>" | "*" | null,
 "text":  "<tresc wypowiedzi>",
 "limit_zdan": <int> | null}
```

- `v` jest w schemacie od poczatku, bo struktura przejdzie do `ask_core` i bedzie miala dwoch
  klientow; wersja bez pola wersji jest wersja, ktorej nie da sie zmienic.
- `repo: "*"` znaczy **swiadomie wszystkie** (kierowca powiedzial „wszystkie projekty" albo reguly
  nie rozstrzygnely). `repo: null` nie wystepuje dla `ask` — patrz rozwidlenie nizej; zostaje
  w schemacie dla `note` / `queue`, gdzie „bez repozytorium" bedzie mialo sens.
- `text` to **cala wypowiedz**, nie resztka po wycieciu nazwy projektu. Wycinanie psuje zdanie
  („co slychac w [] i co dalej"), a model i tak dostaje zakres osobno.
- `limit_zdan` jest `null`, gdy kierowca nie podal liczby. Nie zgadujemy z „krotko" ani „w skrocie":
  domyslny limit trzech zdan jest juz w `SYSTEM`, a liczba wypowiedziana glosno jest jednoznaczna.

## Rozwidlenie: co robic, gdy reguly nie rozpoznaja repozytorium

Wybrane **(a): zapytac wszystkie przez `--add-dir` i pozwolic modelowi wybrac**, czyli zachowac
dzisiejsze zachowanie mostu.

*Dlaczego:* (1) kosztuje zero dodatkowych sekund, podczas gdy dopytanie glosem dokłada pelna
ture (nagranie + transkrypcja + odtworzenie, czyli grubo ponad polowe budzetu 15 s);
(2) jest zgodne z decyzja „nazwij repo w odpowiedzi" — odpowiedz zaczyna sie od nazwy, wiec zle
trafienie slychac od razu, bez pytania; (3) jest to zachowanie **bezpieczne przy blednym parserze**:
najgorsze, co robi nierozpoznanie, to powrot do dzisiejszego czasu odpowiedzi, a nie odpowiedz
o niewlasciwym projekcie. Konsekwencja przyjeta swiadomie: `repo: "*"` jest zarazem „wszystkie"
i „nie wiem", wiec **log musi rozrozniac te dwa przypadki** (pole `repo_reason`: `explicit-all`
albo `no-match`), inaczej pomiar trafnosci nie ma czego liczyc.

## Rezerwa modelowa: nie w tej zmianie, i dlaczego

Prompt dopuszczal model jako rezerwe, gdy reguly nie rozstrzygna. W zakresie `ask` **obie
niepewnosci maja tani wynik domyslny**: nierozpoznana intencja to `ask` (jedyna dzialajaca),
a nierozpoznane repo to `*` (dzisiejsze zachowanie). Rezerwa kosztowalaby wiec kolejne wywolanie
LLM po to, zeby czasem trafic lepiej w rzecz, ktora i tak dziala — przy celu 15 s to zly interes.

Rezerwa wraca jako otwarte pytanie dopiero z `note` / `queue`, gdzie zla intencja **zapisuje** cos
nie tam i nie ma taniego domyslnego wyniku. Zapisane tutaj, zeby nie odkrywac tego drugi raz.

## Dopasowanie nazw repozytoriow

Dane wejsciowe: jedna prawdziwa transkrypcja z logu (2026-09-14) brzmi „w projekcie **Carcha gpt**
integration". Stad trzy wymagania, kazde wynikajace z tego jednego przykladu:

1. **Normalizacja przed porownaniem**: male litery, polskie znaki na ASCII (`zadan` = `zadan`),
   wszystko poza `[a-z0-9 ]` na spacje, spacje sciete. „Carcha gpt" i „car chat gpt" musza trafic
   w ten sam wiersz tablicy.
2. **Dopasowanie po n-gramach slow, nie po calym zdaniu.** Alias „car chat gpt" ma trzy slowa, wiec
   porownujemy go z kazdym trojslowiem wypowiedzi. Porownanie z calym zdaniem topi nazwe w szumie.
3. **Tolerancja literowek**: `difflib.SequenceMatcher` (stdlib, zero zaleznosci) z progiem
   `min_ratio` z pliku danych. „carcha gpt" wobec „car chat gpt" daje okolo 0,9; prog 0,82 jest
   punktem startowym **do zmierzenia** w zadaniu 5.1, nie ustaleniem.

Tablica aliasow jest **danymi** (`poc/aliases.json`): dodanie projektu to jeden wpis, bez zmiany
kodu i bez testu. Nazwy kanoniczne (klucze) musza wystepowac w `~/.claude/monitor_repos.env` —
ta mapa uzupelnia sie sama z hooka `session_start`, wiec jest jedynym zrodlem prawdy o tym, jakie
repozytoria ta maszyna w ogole zna. Alias wskazujacy na nieznane repo jest **wypisywany do logu
przy starcie**, a nie po cichu ignorowany: to zwykle literowka w JSON-ie.

Aliasy sa tez celowo **krotkie i mowione**: „jot ka", „projekt jk", „ribnikster" — to sa formy,
ktore padaja w aucie, a nie nazwy katalogow.

## Zawezenie zakresu = jedyny zysk czasowy

Gdy `repo` jest rozpoznane, `claude -p` startuje w tym katalogu i **nie dostaje pozostalych przez
`--add-dir`**. Model przestaje przeszukiwac cztery drzewa zamiast jednego. To jest hipoteza
z prerejestracji 5.2, nie fakt — dlatego ma warunek negatywu i osobny pomiar. Jesli zysk nie
istnieje, zawezenie i tak zostaje (mniejsza szansa na odpowiedz z cudzego repo), ale nie wolno
go raportowac jako przyspieszenia.

## Odmowa zapisu brzmi jak zdanie, nie jak blad

`note` i `queue` zwracaja **HTTP 200** z jednym zdaniem po polsku. Powod jest praktyczny: skrot
na iPhonie karmi tresc odpowiedzi prosto do `Speak Text`, a kod bledu skonczylby sie cisza albo
komunikatem systemowym po angielsku. Kierowca ma uslyszec, dlaczego nic sie nie stalo.

## Czego ta warstwa nie robi

- Nie rozmawia wieloturowo (kazda wypowiedz jest samodzielna).
- Nie zapisuje niczego na dysk poza logiem mostu.
- Nie zmienia `for_speech`, `sync_all` ani niczego w `poc/deploy/`.
