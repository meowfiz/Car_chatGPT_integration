# HANDOFF — most pytań „głos w aucie → Claude → odpowiedź głosem"

Plik: `poc/ask_server.py` (jeden plik, do wyrzucenia po PoC). Stan: **ścieżka tekstowa działa
i jest zmierzona**, ścieżka audio czeka na pierwszy test z telefonu.

## Zmierzone 2026-09-14 (maszyna `desktop-ffshioa`, Windows, i7 + RTX 3060, transkrypcja na CPU)

| próba | wejście | model | STT | pełna pętla | odpowiedź |
|---|---|---|---|---|---|
| 1 | tekst | sonnet | — | **13,8 s** | poprawna (30 z 31 zadań, następne 1.2 i 1.3) |
| 2 | audio PL, 15 s | sonnet | 6,6 s (z ładowaniem modelu) | **24,2 s** | poprawna (28 z 31, następne 1.3) |
| 3 | audio PL, 15 s | sonnet | **2,1 s** (model ciepły) | 34,5 s | poprawna |
| 4 | tekst | haiku | — | 20,1 s | poprawna co do liczb |

Wnioski z tych czterech prób:

- **Transkrypcja nie jest wąskim gardłem**: 2,1 s na piętnastosekundowe nagranie, model `small`, sam
  procesor. Jakość polskiego dobra; myli tylko angielską nazwę projektu („Carcha gpt").
- **Wąskim gardłem jest Claude czytający pliki**: od 13 do 34 s, bo za każdym razem sam szuka
  w repozytoriach. Szybszy model nie pomógł, bo koszt siedzi w narzędziach, nie w generowaniu.
- **Próg 15 s z OpenSpec jest dziś nietrafiony.** Kierunek naprawy: budować gotowy kontekst po stronie
  mostu (zawartość `openspec/STATUS.md`, nagłówków `notes/start.md` i ostatnich commitów) i wkładać go
  do promptu, żeby model nie musiał niczego szukać. Do zmierzenia w następnej kolejności.
- GPU do transkrypcji **nie jest potrzebne**.

## Gdzie to ma stać

Most musi działać na maszynie, która **jest wybudzona i ma sklonowane repozytoria oraz Claude Code**.
Raspberry Pi z Home Assistantem tego nie uciągnie: nie ma tam repozytoriów, nie ma Claude Code,
a transkrypcja Whisperem zajęłaby mu wielokrotność czasu nagrania.

**Rekomendacja: pecet w pracy, ten stale włączony.** Wymagania na nim:

1. Tailscale zalogowany na to samo konto (jest).
2. Python 3.11 lub nowszy.
3. Claude Code zainstalowany i zalogowany (`claude --version`).
4. Sklonowane repozytoria w jednym katalogu, np. `D:\claude_projects`, i **regularny `git pull`**,
   inaczej odpowiedzi będą ze starego stanu.
5. `pip install faster-whisper` dla ścieżki audio.
6. Karta graficzna nie jest wymagana. Z GPU transkrypcja jest szybsza, na samym procesorze model
   `small` też wystarczy — do wyboru zmienną `ASK_WHISPER`.

Maszyna z pokoju (`desktop-ffshioa`, `100.95.41.116`) nadaje się do testów na biurku, ale zasypia,
więc do auta się nie nadaje.

## Wdrożenie na pececie w pracy (24/7, ciemne monitory)

Pełny scenariusz i narzędzia: **`poc/deploy/README_PRACA.md`** — diagnoza (`00_check.ps1`),
zasilanie (`01_power.ps1`), trzy zadania Harmonogramu (`02_install_tasks.ps1`: most przy starcie
systemu, watchdog co 5 min, `git pull --ff-only` co godzinę), skrót `Ctrl+Alt+Q` gaszący ekrany
(`install_shortcut.ps1`), pomiar (`check_bridge.ps1`) i wycofanie (`99_uninstall.ps1`).
Sekret i konfiguracja w `%USERPROFILE%\.claude\ask_bridge.env` (wzór: `poc/deploy/bridge.env.example`),
nigdy w repo.

## Uruchomienie mostu

```powershell
$env:ASK_SECRET = "dlugi-losowy-ciag"       # to laduje w adresie URL
$env:ASK_BIND   = "100.95.41.116"           # adres Tailscale TEJ maszyny
$env:ASK_PORT   = "8787"
$env:ASK_ROOT   = "D:\claude_projects"      # katalog z repozytoriami
$env:ASK_MODEL  = "sonnet"                  # albo opus, gdy ma myslec dluzej
python poc\ask_server.py
```

Sprawdzenie z tej samej maszyny:

```bash
curl http://100.95.41.116:8787/health
curl -X POST -H "Content-Type: application/json" \
     --data '{"q":"Co slychac w projekcie HA?"}' \
     "http://100.95.41.116:8787/ask/dlugi-losowy-ciag?format=json"
```

Log każdego wywołania: `project_files/run_files/ask_server.log` (poza repozytorium, zgodnie z 2.5).

## Skrót na iPhonie — dokładne kroki

Najpierw **wariant tekstowy**, bo sprawdza całą pętlę bez Whispera i bez ryzyka z nagrywaniem.

### Skrót „Monitor” (wersja 1, dyktowanie Apple)

1. Aplikacja Skróty → plus w prawym górnym rogu → Zmień nazwę na **Monitor** (nazwa po angielsku,
   bo wypowie ją Siri, która polskiego nie zna).
2. Dodaj akcję **Dyktuj tekst**. W jej ustawieniach ustaw język **polski**, a „Zatrzymaj nasłuchiwanie”
   na **Po pauzie**.
3. Dodaj akcję **Pobierz zawartość URL**. Wpisz adres:
   `http://<adres-tailscale-peceta>:8787/ask/<twoj-sekret>`
   Rozwiń **Pokaż więcej** i ustaw:
   - Metoda: **POST**
   - Nagłówki: `Content-Type` = `application/json`
   - Treść żądania: **JSON**, jedno pole tekstowe o kluczu `q`, a jako wartość wstaw zmienną
     **Dyktowany tekst**.
4. Dodaj akcję **Wypowiedz tekst** i jako treść ustaw wynik z poprzedniej akcji. W jej ustawieniach
   wybierz głos **polski**.
5. Zapisz. Uruchom raz z aplikacji, żeby zatwierdzić pytanie o dostęp do sieci lokalnej.
6. Powiedz „Hey Siri, Monitor”, a po sygnale zadaj pytanie po polsku.

### Skrót „Monitor Audio” (wersja 2, Whisper)

Ta sama konstrukcja, z dwiema różnicami:

- zamiast **Dyktuj tekst** dodaj **Nagraj dźwięk**; w ustawieniach akcji ustaw **Rozpocznij od razu**
  i **Zatrzymaj po** ustalonym czasie, na start 8 sekund;
- w akcji **Pobierz zawartość URL** ustaw nagłówek `Content-Type` na `audio/m4a`, a **Treść żądania**
  na **Plik** i wskaż nagranie z poprzedniej akcji.

Adres i reszta bez zmian. Jeśli Siri uruchomi skrót, a nagrywanie zawiesi się albo poprosi
o dotknięcie ekranu, wracamy do wersji 1 i zapisujemy to jako wynik pomiaru.

## Bezpieczeństwo tego mostu

- Nasłuchuje wyłącznie na adresie Tailscale, nie na `0.0.0.0`, więc z internetu jest niewidoczny.
- Sekret siedzi w ścieżce URL; zły adres dostaje 403 i wpis w logu.
- Limit tempa: jedno wywołanie na 3 sekundy, maksymalnie sześćdziesiąt na godzinę.
- Claude dostaje wyłącznie narzędzia do odczytu. Zapis, edycja plików, `git add`, `git commit`
  i `git push` są zablokowane, podobnie jak sięganie do sieci.
- Odpowiedź jest czyszczona z markdownu i przycinana do siedmiuset znaków, żeby nadawała się do
  przeczytania na głos.

## Znane potknięcia z pierwszego uruchomienia

- `--permission-prompt-tool none` nie istnieje w tej wersji Claude Code (2.1.270) i wywalało każde
  wywołanie; usunięte, w trybie `-p` wszystko, co wymagałoby pytania, i tak jest odrzucane.
- `MultiEdit` nie jest nazwą znanego narzędzia i cała lista blokad była przez to odrzucana.
- **ctranslate2 4.8.2 wywala interpreter** (naruszenie ochrony pamięci) przy ładowaniu modelu na tej
  maszynie. Działa po `pip install ctranslate2==4.5.0`. Wersję trzeba przypiąć na maszynie docelowej.
- **Transkrypcja uruchamiana z wątku serwera zabija cały proces** — to samo naruszenie ochrony pamięci,
  którego nie łapie żaden `try`. Dlatego model chodzi w osobnym procesie roboczym; awaria kosztuje
  jedno pytanie, nie serwer.
- Uruchamianie serwera z Git Basha kończyło się tym samym wywrotem; z PowerShella działa.
- Port zajęty przez poprzednią instancję nie daje czytelnego błędu; przy testach zmieniaj port.
- Zostawione po testach serwery nasłuchują na 8793 i 8794 — zamknij okna, zanim uruchomisz wersję
  docelową.
