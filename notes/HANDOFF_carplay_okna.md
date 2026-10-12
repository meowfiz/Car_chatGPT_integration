# HANDOFF — CarPlay okna projektow (zmiana `carplay-okna-projektow`)

Punkt wejscia do tematu „powiedziec w aucie 'projekt X: <polecenie>' i uslyszec odpowiedz".
Stan: **endpoint PoC gotowy, pomiar nierozpoczety** (2026-10-12).

Zmiana OpenSpec: `openspec/changes/carplay-okna-projektow/`.
Powiazane: `openspec/changes/poc-carplay-command/` (one-shot `claude -p` — inna sciezka,
dziedziczymy pomiary Whisper/transkrypcji polskiej z `notes/HANDOFF_most_pytan.md`).

## Infrastruktura, do ktorej sie podlaczamy

- Bramka glosowa: `tools/voice_gateway.py` w repo `project_integration`, port **8788**, TLS
  z `~/.claude/certs/desktop-geih38c.taileb4004.ts.net.{crt,key}`, bind na adres tailnetowy
  (patrz `discover_tls()`).
- URL bazowy skrotu: **`https://desktop-geih38c.taileb4004.ts.net:8788`** (lokalny tailnet,
  bez wystawiania w publiczny internet). Weryfikacja: `curl -sS https://desktop-geih38c.taileb4004.ts.net:8788/health`
  z telefonu z aktywnym Tailscale.
- Endpoint PoC: `GET /api/car/test-audio` → zwraca `audio/mpeg` z nagranym po polsku
  „test glosu w aucie" (edge-tts). Bez tokenu, bind tylko na tailnet. **Do usuniecia po
  pomiarze** (task 7.1 w zmianie).

## 1.1 Shortcut iOS „CarPlay audio test"

Jednorazowy skrot do zmierzenia, czy CarPlay odtworzy audio z HTTPS tailnetu w glosniku auta.
Buduje sie go **raz**, kasuje po PoC (razem z endpointem).

### Krok po kroku na iPhone (polski interfejs iOS)

1. Otwórz aplikację **Skróty**.
2. Zakładka **Moje skróty** (dolna belka) → `+` w prawym górnym rogu.
3. Pole „Nazwa skrótu" u góry: **`CarPlay audio test`** (angielskie słowa, bo Siri
   rozpoznaje angielskie nazwy pewniej niż polskie).
4. Dodaj dwie akcje po kolei (pasek wyszukiwania na dole, „Szukaj czynności"):

   | nr | wyszukaj po polsku | wybierz czynność | ustaw tak |
   |---|---|---|---|
   | 1 | `pobierz zawartość` | **Pobierz zawartość adresu URL** | URL: `https://desktop-geih38c.taileb4004.ts.net:8788/api/car/test-audio` <br> Rozwiń **Pokaż więcej** → Metoda: `GET` <br> Nagłówki: puste <br> Treść żądania: puste |
   | 2 | `odtwórz dźwięk` | **Odtwórz dźwięk** | Dźwięk: dotknij pola i wybierz **Zawartość adresu URL** (zmienna z poprzedniej czynności) <br> Głośność: `0,8` <br> Rozwiń → **Czekaj na zakończenie**: włączone |

5. Dotknij ikony `(i)` na dole:
   - **Pokaż w arkuszu udostępniania**: wyłączone.
   - **Używaj z Siri**: włączone (automatycznie — nazwa skrótu jest frazą wywołania).
6. Dotknij **Gotowe** w prawym górnym rogu.

### Weryfikacja na postoju (bez CarPlay)

1. Telefon ma aktywny Tailscale (ikona VPN w pasku statusu).
2. W aplikacji **Skróty** dotknij kafelka `CarPlay audio test` — powinien odtworzyć
   „test glosu w aucie" po polsku, bez komunikatu błędu. Jeśli błąd **certyfikatu / SSL** —
   sprawdź, czy adres w URL to dokładnie `desktop-geih38c.taileb4004.ts.net` (Tailscale
   wystawia cert dla tej nazwy; adres IPv4 nie zadziała).
3. „Hej Siri, CarPlay audio test" na telefonie (bez auta) — powinien odtworzyć to samo
   bez dotykania.

### Skrot B — „CarPlay text test" (fallback, dociaga do konca)

**Dlaczego:** Siri w CarPlay zamyka sesje audio Shortcuta zanim `Odtworz dzwiek` dokonczy
(2026-10-12: na probie w aucie slychac bylo tylko „test" i „test glosu w a..."). Akcja
`Przeczytaj tekst` (`Speak Text`) uzywa wlasnej sesji Siri i dociaga do konca -- cena:
glos **systemowy Siri** zamiast VCC. Mierzymy oba warianty, decyzja po pomiarze.

1. Skroty → `+` → nazwa: **`CarPlay text test`**.
2. Dodaj dwie akcje:

   | nr | wyszukaj po polsku | wybierz czynność | ustaw tak |
   |---|---|---|---|
   | 1 | `pobierz zawartość` | **Pobierz zawartość adresu URL** | URL: `https://desktop-geih38c.taileb4004.ts.net:8788/api/car/test-text` <br> Rozwiń **Pokaż więcej** → Metoda: `GET` |
   | 2 | `przeczytaj tekst` | **Przeczytaj tekst** | Tekst: zmienna **Zawartość adresu URL** <br> Rozwiń → Jezyk: `Polski` <br> Glos: dowolny polski (np. `Zosia`) <br> Czekaj na zakończenie: włączone |

3. `(i)` → **Używaj z Siri**: włączone. **Gotowe**.
4. Test w aplikacji (bez auta) — ma przeczytac „test głosu w aucie" po polsku.

### 1.3 Pomiar w aucie (3 proby, podpiety CarPlay)

Auto na postoju, silnik na, CarPlay zapiety przewodem USB. **Dwie serie:** 3 x Skrot A
(audio), 3 x Skrot B (tekst). Osobne tabele. Pytanie bramkujace: **ktory wariant dociaga
do konca?**

**Seria A — „Hej Siri, CarPlay audio test"** (VCC/Twoj glos, moze sie urwac):

| nr | start [HH:MM] | zagralo pelne zdanie? | ostatnie slyszane slowa | uwagi |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |

**Seria B — „Hej Siri, CarPlay text test"** (glos Siri, powinno dociagnac):

| nr | start [HH:MM] | zagralo pelne zdanie? | zrozumiale po polsku? | uwagi |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |

Zapis takze w logu serwera: `log("car-poc", "test-audio HIT ...")` w `voice_gateway.py` --
latwo potwierdzic po powrocie, ze zapytanie do serwera dotarlo.

### 1.4 Decyzja PoC (bramka reszty zmiany)

Reguła decyzyjna (po pomiarze 2026-10-12, kiedy Skrót A urwal sie na „test"):

- **Skrot A >= 2/3 pelne** → trzymamy VCC/HA glos, idziemy do grupy 2 z tym wariantem.
- **Skrot A < 2/3 pelne, Skrot B >= 2/3 pelne** → akceptujemy glos Siri jako cene za dociagniecie
  do konca; grupa 2 buduje endpoint zwracajacy tekst (`X-Reply-Text`), Shortcut uzywa
  `Przeczytaj tekst`. Zapisujemy jako „ograniczenie techniczne CarPlay" (ZASADY 5.8),
  nie negatyw.
- **Oba < 2/3** → wynik negatywny (ZASADY 5.8), wpis przyczyny tutaj:
  - brak sieci / timeout w aucie → problem Tailscale w LTE/5G,
  - 403 / 404 / cert error → problem bramki (powtorzyc po restarcie
    `monitor/services.py --restart`),
  - cisza w obu → CarPlay blokuje sesje audio Shortcuta w ogole.
  - Dalsze zadania zmiany **nie rozpoczynaja sie** do czasu rozstrzygniecia; endpointy
    `/api/car/test-audio` i `/api/car/test-text` usuwaja sie recznie (task 7.1 w `tasks.md`).

## Co dalej (po zdanej bramce)

- Grupa 2 w `tasks.md`: endpoint `/api/car/command` (parser „projekt X: ...", `tmux send-keys`,
  `capture-pane` na `Glosowo:`).
- Grupa 5: wlasciwy Shortcut „Projekt" (`Dictate Text` lub `Record Audio` — wybor po
  pomiarze w `poc-carplay-command 3.5`).
- Grupa 6: prerejestracja i jazda pomiarowa.

## Historia zmian pliku

- 2026-10-12 — utworzony, bramka PoC gotowa, pomiar w aucie przed uzytkownikiem.
