## Context

Stan na 2026-09-14 (szczegóły i źródła: `notes/research/2026-09-14-mechanizmy-carplay.md`):

- ChatGPT w CarPlay (iOS 26.4+, wszystkie plany) to izolowana aplikacja głosowa: bez wake worda, bez
  dostępu do innych aplikacji; **tryb głosowy nie obsługuje apps**, MCP/Developer mode jest web-only
  i nie obejmuje planu Go. Nie ma więc dziś „wyzwalacza” z ChatGPT Voice do własnego endpointu.
- Siri działa hands-free w CarPlay i uruchamia skróty po nazwie. Aplikacja HA Companion wystawia App
  Intents: `Assist prompt`, `Perform action`, `Activate scene`, `Run script`. Skrót może czytać wynik
  przez `Speak Text`.
- **Siri nie obsługuje polskiego** (2026-09-14; polskiego nie ma na liście języków Siri ani Apple
  Intelligence). Rozmowa po polsku musi więc omijać Siri wszędzie poza frazą budzącą: dyktowanie iOS
  obsługuje polski niezależnie od języka Siri, a akcja `Dictate Text` przyjmuje kod locale (`pl_PL`).
  Polskie głosy systemowe (np. „Zosia”) są dostępne dla `Speak Text`.
- HA Companion 26.4+ ma też Assist bezpośrednio w CarPlay, ale start wymaga dotknięcia.
- Infrastruktura istnieje: HA OS na RPi 4 w tailnecie, aplikacja HA na iPhonie, repo `HA` z konfiguracją.

Ograniczenie użytkownika: plan ChatGPT Go (PDF, str. 2) oraz wymaganie rozmowy po polsku. Model iPhone'a
i to, czy ma Apple Intelligence (warunek akcji „Use Model”), nieznane — do sprawdzenia w zadaniu 1.1.

## Goals / Non-Goals

**Goals:**
- Potwierdzić lub obalić, że **polskie** polecenie głosowe hands-free w jadącym aucie uruchamia akcję w HA
  i wraca **polską** odpowiedzią głosową, z liczbami: udane/wszystkie, poprawność transkrypcji, czas do
  akcji, czas do odpowiedzi.
- Zrobić to bez kodu, w jednej sesji konfiguracji i jednej sesji pomiarowej w aucie.
- Zostawić decyzję „czy i na jakim moście budować Command Center” opartą na pomiarze.

**Non-Goals:**
- Command Center, MCP, integracje GitHub/Claude Code/komputery.
- Własna aplikacja iOS z entitlementem CarPlay.
- Zmiana planu ChatGPT (research pokazał, że nie odblokowałaby trybu głosowego).
- Rozmowa wieloturowa; PoC to jedno polecenie = jedno wywołanie.

## Decisions

**D1. Most = Siri + Skróty, nie ChatGPT Voice.** Jedyna ścieżka, która dziś działa hands-free bez własnej
aplikacji i bez planu wyżej. Alternatywy odrzucone: ChatGPT apps/MCP (nie działa w głosie, web-only),
własna aplikacja CarPlay (tygodnie, recenzja Apple, i tak start dotknięciem), Assist w CarPlay przez
dotknięcie (nie jest hands-free; zostaje jako fallback B).

**D2. Wejście do HA = App Intent `Assist prompt`, nie webhook.** Assist prompt daje rozumienie języka
naturalnego po stronie HA i zwraca tekst odpowiedzi do przeczytania; webhook wymagałby sztywnego
mapowania fraz w skrócie. Alternatywa `Activate scene` na stałe zostaje jako fallback A: rozdziela
problem „czy Siri w ogóle uruchamia skrót i czyta odpowiedź w aucie” od problemu „czy Assist rozumie”.

**D3. Agent konwersacyjny Assist: wbudowany HA do kalibracji, OpenAI Conversation jako cel.** Wbudowany
agent nie wymaga kluczy i wystarcza do sceny, więc służy do zmierzenia samej pętli. Docelowo rozmowa ma
być z ChatGPT (decyzja użytkownika 2026-09-14, przyjęta jako pewnik), a **agent LLM w HA to jedyne
miejsce, w którym da się to dziś zrobić z narzędziami**: skrypty HA są wystawiane agentowi jako tools,
więc GPT słucha po polsku, wybiera narzędzie i wywołuje akcję. Mierzyć osobno, nie mieszać konfiguracji
(reguła 6.2). Cena: to GPT przez API, płatne per token, bez pamięci i osobowości konta ChatGPT.

**D6. Most do Claude'a jest narzędziem agenta, nie osobnym mostem głosowym.** `script.claude_task` →
`rest_command` → mały endpoint uruchamiający `claude -p` i zwracający tekst; przy długim zadaniu endpoint
odpowiada natychmiast „przyjąłem, wynik pod <link>”, a wynik dociera powiadomieniem HA. Odrzucone:
liczenie na to, że ChatGPT sam otworzy link z wynikiem (patrz D7). Endpoint przyjmuje **polecenia
z zamkniętej listy**, bo publiczny URL uruchamiający agenta na moim komputerze to zdalne wykonanie kodu,
a treść wracająca z sieci jest wektorem pośredniego prompt injection.

**D7. „ChatGPT sam woła mój URL” zostaje eksperymentem E1, nie fundamentem.** Kanał istnieje (agent
`ChatGPT-User` pobiera stronę na prośbę użytkownika, robots.txt go nie wiąże), ale w trybie głosowym jest
to jedyne wyjście na zewnątrz i jest niewspierane: GPT-Live nie obsługuje connected apps ani pluginów,
a rozmowy z własnym GPT z Actions spadają do Advanced Voice bez akcji. Dodatkowo: tylko GET, sekret
musiałby siedzieć w ścieżce, adres trzeba wypowiedzieć, brak potwierdzenia wykonania, odpowiedź wraca
jako streszczenie modelu. Dlatego E1 jest półgodzinnym testem rozstrzygającym (zadania 4.3–4.4), a nie
założeniem architektury.

**D4. Skrót „Home”: `Dictate Text` (`pl_PL`) → `Assist prompt` → `Speak Text` (głos polski).** Nazwa
angielska i jednowyrazowa, bo Siri musi ją rozpoznać w swoim języku; jeden skrót obsługuje wszystkie
polecenia. Odrzucone: `Ask for Input` (Siri zapyta i będzie słuchać po angielsku — polskie polecenie
przepisze na bełkot); osobny skrót na każde polecenie (nie skaluje się, ale to jest dokładnie fallback A);
zmiana języka Siri na polski (nie istnieje).

**D4a. Podział języków jest świadomy i mierzony osobno.** Po angielsku: dwa słowa frazy budzącej. Po
polsku: polecenie (dyktowanie `pl_PL`), rozumienie (Assist w HA), odpowiedź (`Speak Text`, głos polski).
Ponieważ warstwa rozpoznawania mowy jest teraz apple'owym dyktowaniem, a nie Siri, jakość transkrypcji
w hałasie auta jest osobnym mierzonym wynikiem — fallback B (Assist w CarPlay, STT po stronie HA) służy
jako punkt odniesienia dla tej samej wypowiedzi.

**D5. Pomiar: stoper + logbook HA, nie „na oko”** (reguła 5.2). Czas do akcji = znacznik `last_changed`
sceny w HA minus znacznik końca wypowiedzi (nagranie dyktafonem z timestampem albo drugi telefon ze
stoperem). Czas do odpowiedzi = z tego samego nagrania. Zapis do tabeli od pierwszej próby.

**D6. Prerejestracja progu zaliczenia przed jazdą** (reguła 3.3 w wersji dla pomiaru opisowego): PoC
zaliczony przy ≥ 7/10 udanych i medianie czasu do akcji ≤ 10 s; poniżej — negatyw z przyczyną.

## Przepływ

```
kierowca ──"Hey Siri, Home"──▶ Siri (CarPlay, mikrofon auta)   [jedyny fragment po angielsku]
                              │ uruchamia skrót "Home"
                              ▼
                     Skrót: Dictate Text (pl_PL) ◀── kierowca mówi PO POLSKU
                              │ tekst polecenia (polski)
                              ▼
                     App Intent HA: Assist prompt (pipeline "poc", jezyk polski)
                              │ HTTPS (Tailscale / zewnętrzny URL HA)
                              ▼
                     Home Assistant ── conversation.process ──▶ scene.turn_on
                              │ tekst odpowiedzi (polski)        (logbook: t_akcja)
                              ▼
                     Skrót: Speak Text (głos polski) ──▶ głośniki auta (t_odpowiedz)
```

Fallback A: `Dictate Text` i `Assist prompt` zastąpione przez `Activate scene` + stały polski tekst
(sprawdza pętlę bez rozpoznawania mowy).
Fallback B: HA Companion → CarPlay → Quick Access → Assist (dotknięcie) → ten sam pipeline; w pełni po
polsku, STT po stronie HA, ale bez hands-free.

## Risks / Trade-offs

- [`Dictate Text` uruchomione przez Siri w CarPlay nie startuje, nie kończy się samo albo wymaga
  dotknięcia „Gotowe”] → sprawdzić najpierw na postoju (zadanie 2.3); jeśli pada, PoC leci fallbackiem A,
  a wynik jest zapisany jako ograniczenie mostu. To jest ryzyko nr 1.
- [`Dictate Text` ignoruje parametr `pl_PL` na iOS 26 i dyktuje po angielsku] → potwierdzić na postoju
  z tekstem wyświetlonym przed wysłaniem (`Show Result`); jeśli nie da się wymusić locale, alternatywa:
  polska klawiatura jako domyślna dyktowania, a jeśli i to nie — ścieżka główna upada na rzecz fallbacku B.
- [Transkrypcja polska psuje się w hałasie 70+ km/h] → mierzone osobno (kolumna „transkrypcja OK”);
  fallback B na tej samej wypowiedzi daje porównanie ze STT Home Assistanta.
- [HA nieosiągalny z auta: Tailscale na iPhonie nieaktywny lub URL zewnętrzny nie działa przez LTE] →
  zadanie 1.3 sprawdza oba URL-e z LTE przed jazdą; zapisać, który użyto.
- [Assist nie rozumie polskiego polecenia mimo poprawnej transkrypcji] → pipeline z językiem polskim;
  alias sceny „scena testowa”; osobno zmierzyć agenta LLM (D3), który radzi sobie z polską odmianą lepiej
  niż intencje wbudowane.
- [Speak Text nie gra przez audio auta albo czyta polski tekst angielskim głosem] → wybrać głos polski
  jawnie w akcji; znane problemy z wyjściem audio z wątku HA Community; zapisać jako wynik.
- [Pomiar zaniżony/zawyżony przez ręczny stoper] → nagranie audio z timestampem + logbook HA; podać
  niepewność ±1 s.
- [Konfiguracja HA zostawia śmieci] → wszystko pod jedną nazwą `poc_carplay_*`, usuwalne jednym ruchem.

## Open Questions

- Model iPhone'a i iOS (≥ 26.4? Apple Intelligence?) — decyduje o fallbacku B i akcji „Use Model”.
- Na jaki język ustawiona jest dziś Siri na tym iPhonie i czy „Hey Siri” jest włączone przy zablokowanym
  ekranie oraz w CarPlay.
- Czy `Dictate Text` na iOS 26 nadal przyjmuje kod locale jako wejście (źródło [S21] jest starsze).
- Czy HA ma skonfigurowany TTS (Piper / cloud) — potrzebny tylko dla fallbacku B; ścieżka główna czyta
  przez Siri.
- Rozstrzygnięte 2026-09-14: agent OpenAI Conversation wchodzi do PoC (grupa zadań 4), bo rozmowa ma być
  z ChatGPT. Do ustalenia zostaje klucz API i limit kosztu na miesiąc.
- Gdzie stanie endpoint mostu do Claude'a: dodatek HA obok `project_monitor` czy kontener na komputerze
  w tailnecie (ten drugi jest bliżej repozytoriów, ale musi być wybudzony).
