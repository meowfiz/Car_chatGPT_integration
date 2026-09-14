## Context

Stan na 2026-09-14, po dwóch turach researchu (`notes/research/2026-09-14-mechanizmy-carplay.md`,
`notes/research/2026-09-14-chatgpt-jako-wyzwalacz.md`) i po doprecyzowaniu celu przez użytkownika.

Cel: w samochodzie zadać pytanie po polsku i dostać odpowiedź głosem — o stan dowolnego projektu,
o repozytoria, o Home Assistanta. Mózgiem ma być Claude, bo ma dostęp do repozytoriów i jest opłacony.

Twarde ograniczenia zastane:

- Aplikacja ChatGPT w trybie głosowym nie ma wyjścia do własnego endpointu (apps i pluginy wyłączone,
  własne GPT z Actions bez akcji). Nie może być mostem ani wyzwalaczem.
- Subskrypcja ChatGPT Go nie daje dostępu do API; integracja OpenAI w HA to osobne, płatne konto.
- Siri nie zna polskiego. Może natomiast uruchomić skrót po **angielskiej** nazwie i to jedyna rola,
  jaką dostaje.
- W CarPlay nie ma wake worda dla aplikacji innych niż Siri; aplikacje głosowe startują dotknięciem.
- Repo `HA` ma zasadę „zero cloud dla głosu i automatyzacji": STT to Speech-to-Phrase ze **statycznym
  słownikiem** (rozpoznaje tylko frazy z `sentences.yaml`), TTS to Piper, wake word openWakeWord.
  Do swobodnych pytań ten potok się nie nadaje i nie należy go psuć.
- Dopasowanie intencji w HA jest czułe na diakrytyki (pomiar w repo `HA` z 2026-09-14).
- project_monitor już wystawia API z autoryzacją tokenem: stan wszystkich repozytoriów, zadania
  i zdarzenia per repozytorium, strumień na żywo, publikowanie sensorów do HA.

## Goals / Non-Goals

**Goals:**
- Zmierzyć, czy pytanie po polsku zadane w jadącym aucie wraca sensowną odpowiedzią głosową
  z project_monitora, z liczbami: udane/wszystkie, poprawność transkrypcji, czas do odpowiedzi.
- Zrobić to bez agenta chmurowego w HA i bez nowego abonamentu.
- Zostawić decyzję o Command Center opartą na pomiarze.

**Non-Goals:**
- Utrzymywany Command Center, MCP, sterowanie GitHubem i uruchamianie zadań zapisujących.
- Własna aplikacja iOS z entitlementem CarPlay.
- Zastępowanie lokalnego potoku głosowego w HA.
- Rozmowa wieloturowa; PoC to jedno pytanie i jedna odpowiedź.

## Decisions

**D1. Siri jest wyłącznie wyzwalaczem, nie rozpoznaje mowy.** Słyszy dwa angielskie słowa („Hey Siri,
Monitor"). Odrzucone: czekanie na polską Siri (nie istnieje, terminy spekulacyjne), zmiana języka
systemu, rezygnacja z hands-free.

**D2. Rozpoznawanie polskiej mowy robi Whisper, nie Apple i nie Siri.** Skrót nagrywa dźwięk akcją
`Record Audio` o **stałej długości** i wysyła plik do project_monitora; transkrypcja leci przez
faster-whisper na komputerze w tailnecie, a przy jego braku przez API transkrypcji. To jest ten sam
rodzaj modelu, dzięki któremu ChatGPT „perfekcyjnie zbiera polski głos" — tyle że wywołany samodzielnie.
Wzorzec jest sprawdzony przez innych: publikowane skróty „nagraj i przepisz Whisperem" istnieją od lat.
Odrzucone: `Dictate Text` jako warstwa główna (zachowanie akcji bywa niespójne zależnie od kontekstu
uruchomienia) — zostaje jako wariant zapasowy A.

**D3. Mózgiem jest Claude przez project_monitor, nie model w Home Assistancie.** `claude -p` na komputerze
z dostępem do repozytoriów w trybie tylko do odczytu, wywoływany przez nowy endpoint obok istniejącego
API monitora. Odrzucone: agent OpenAI Conversation w Assist — łamie zasadę offline repo `HA`, wymaga
nowego płatnego konta i daje gorszy dostęp do repozytoriów niż Claude, który już tam sięga.

**D4. Home Assistant zostaje mikrofonem i głośnikiem, nie mózgiem.** Potok offline HA pozostaje
nietknięty; scena testowa i jej alias idą przez `voice/voice_data.yaml` i generator, bo to jedyne źródło
prawdy dla komend. Skrypty i scenę trzeba wyeksponować do Assist ręcznie.

**D5. Odpowiedź czytana polskim głosem systemowym iOS** w akcji `Speak Text`. Piper z HA nie wchodzi
w tę ścieżkę, bo dźwięk ma iść przez telefon do audio auta.

**D6. Endpoint pytań jest tylko do odczytu i ma zamkniętą listę operacji.** Sekret w ścieżce, limit
tempa, log każdego wywołania, brak uprawnień do zapisu i do `git push`. Publiczny adres uruchamiający
agenta to zdalne wykonanie kodu, a treść wracająca z sieci to wektor pośredniego prompt injection.

**D7. „ChatGPT sam woła mój URL" zostaje eksperymentem E1.** Kanał istnieje (agent `ChatGPT-User` pobiera
stronę na prośbę użytkownika), ale w trybie głosowym jest niewspierany. Test rozstrzyga, negatyw zamyka
temat.

**D8. Próg zaliczenia zadeklarowany przed pomiarem.** Ścieżka główna: ≥ 7/10 udanych prób, mediana czasu
od końca wypowiedzi do początku odpowiedzi ≤ 15 s, ≥ 8/10 poprawnych transkrypcji. Próg czasu jest
luźniejszy niż przy scenie, bo w pętli siedzi model czytający repozytoria.

## Przepływ

```
kierowca ──"Hey Siri, Monitor"──▶ Siri (CarPlay)      [jedyne dwa slowa po angielsku]
                                   │ uruchamia skrot
                                   ▼
                          Record Audio (stala dlugosc) ◀── pytanie PO POLSKU
                                   │ plik audio
                                   ▼
                          project_monitor  POST /api/ask   [token + sekret, limit tempa, log]
                                   │
                                   ├── faster-whisper (komputer w tailnecie) ──▶ tekst PL
                                   │
                                   └── claude -p (tylko odczyt repozytoriow) ──▶ odpowiedz PL
                                   │        zrodla: /api/state, tasks, events, notes, git
                                   ▼
                          Skrot: Speak Text (glos polski) ──▶ glosniki auta
```

Wariant zapasowy A: `Dictate Text` z locale `pl_PL` zamiast nagrania (bez Whispera, szybciej, gorzej
w hałasie). Wariant zapasowy B: dotknięcie Assist w aplikacji HA w CarPlay — w pełni po polsku, ale STT
to Speech-to-Phrase, więc **tylko wcześniej zadeklarowane frazy**; służy jako punkt odniesienia, nie jako
droga do swobodnych pytań.

## Risks / Trade-offs

- [`Record Audio` uruchomione przez Siri zawiesza się albo wymaga dotknięcia „Stop"] → udokumentowane
  skargi; dlatego stała długość nagrania i test na postoju przed jazdą. Jeśli padnie, wchodzi wariant A.
  To jest ryzyko nr 1.
- [Stała długość nagrania ucina długie pytanie albo każe czekać po krótkim] → zmierzyć dwie długości
  (np. 6 s i 10 s) i wybrać po wynikach, nie po wrażeniu.
- [Transkrypcja polska psuje się w hałasie 70+ km/h] → osobna kolumna w tabeli prób; porównanie Whisper
  kontra `Dictate Text` na tych samych nagraniach.
- [Brak diakrytyków psuje dopasowanie intencji w HA] → dotyczy tylko poleceń do HA; pytania do monitora
  idą do modelu, który odmiany wybacza.
- [Komputer z Whisperem i Claude'em śpi] → PoC wymaga jednej maszyny wybudzonej; zapisać, której.
- [Czas odpowiedzi rośnie przez model czytający repozytoria] → wariant „przyjąłem, wynik powiadomieniem"
  mierzony osobno.
- [Publiczny endpoint to zdalne wykonanie kodu] → D6; dodatkowo PoC może działać wyłącznie w tailnecie,
  bo iPhone jest w tej samej sieci; publiczny adres potrzebny jest tylko dla E1.

## Open Questions

- Czy iPhone w aucie ma aktywny Tailscale — jeśli tak, endpoint nie musi być publiczny w ogóle.
- Wersja aplikacji HA Companion (warunek wariantu B, wymaga 26.4+).
- Która maszyna w tailnecie hostuje Whispera i `claude -p`, i czy ma być wybudzana automatycznie.
- Jakie uprawnienia dostaje `claude -p`: same pliki repozytoriów czy też polecenia `git log`.
