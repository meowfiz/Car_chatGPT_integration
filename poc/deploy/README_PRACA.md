# Wdrożenie mostu na pececie w pracy — scenariusz na 30 minut

Cel: komputer w pracy stoi włączony 24/7, **monitory są ciemne**, a most `poc/ask_server.py`
odpowiada z tailnetu, także po restarcie i bez zalogowanej sesji.

Założenia (potwierdzone 2026-09-15): **Windows 11/10 Pro, lokalny admin, brak domeny.**
Jeśli któreś przestanie być prawdą — patrz „Gdy coś jest inaczej" na końcu.

---

## Zanim pojedziesz do pracy (5 min, na tej maszynie)

1. Wygeneruj sekret i zapisz go **poza repo** — będzie w adresie URL skrótu na iPhonie:

   ```powershell
   [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
   ```

2. Weź ze sobą: ten katalog (`poc/deploy/`, jest w repo — wystarczy `git pull` w pracy),
   sekret, hasło do konta Windows na pececie w pracy.

---

## W pracy — kolejność, nic nie pomijaj

### Krok 0. Diagnoza (2 min, zwykły PowerShell)

```powershell
cd D:\claude_projects\Car_chatGPT_integration\poc\deploy
powershell -NoProfile -ExecutionPolicy Bypass -File .\00_check.ps1
```

Skrypt **niczego nie zmienia**. Na końcu wypisuje listę `TODO:` — to jest twoja lista braków.
Typowe braki i jak je zamknąć:

| brak | co zrobić |
|---|---|
| `python missing` | `winget install Python.Python.3.12`, nowa konsola |
| `node missing` / `claude code missing` | `winget install OpenJS.NodeJS.LTS`, potem `npm i -g @anthropic-ai/claude-code` |
| `claude never logged in` | uruchom `claude` raz w konsoli i zaloguj się (to jedyny krok, którego nie da się zautomatyzować) |
| `faster_whisper MISSING` | `pip install faster-whisper "ctranslate2==4.5.0"` — **wersja ctranslate2 przypięta celowo**, 4.8.2 wywalała interpreter (HANDOFF) |
| `tailscale not logged in` | zaloguj Tailscale na to samo konto, sprawdź `tailscale ip -4` |
| `ASK_ROOT does not exist` | sklonuj repozytoria z `repos.txt` do `D:\claude_projects` |
| `env file missing` | patrz krok 1 |

### Krok 1. Plik z konfiguracją (2 min)

```powershell
copy .\bridge.env.example "$env:USERPROFILE\.claude\ask_bridge.env"
notepad "$env:USERPROFILE\.claude\ask_bridge.env"
```

Wypełnij `ASK_SECRET` (ten wygenerowany), sprawdź `ASK_ROOT`. Reszta ma sensowne domyślne.
`ASK_BIND` zostaw pustą — most sam weźmie adres Tailscale przy starcie, więc zmiana adresu
niczego nie psuje. **Ten plik nigdy nie trafia do repo.**

### Krok 2. Zasilanie: ma nie zasypiać, ma gasić ekrany (1 min, PowerShell jako admin)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\01_power.ps1
```

Co robi i dlaczego akurat to:

- `monitor-timeout-ac 5` — monitory same gasną po 5 minutach bezczynności (parametr `-MonitorMinutes`);
- `standby-timeout-ac 0`, `hibernate-timeout-ac 0`, `disk-timeout-ac 0` — komputer nie zasypia nigdy;
- **`unattended sleep timeout = 0`** — to jest pułapka, na którą wpada większość ludzi: po zdalnym
  wybudzeniu Windows usypia maszynę po 2 minutach **mimo** ustawienia „nigdy" w zwykłym uśpieniu;
- `powercfg /hibernate off` — nie ma pliku hibernacji, więc nie ma hybrydowego snu ani szybkiego
  rozruchu, które potrafią zatrzymać maszynę mimo powyższych (`-KeepHibernate` zostawia);
- karty sieciowe tracą prawo usypiania się (inaczej Tailscale znika cicho);
- USB selective suspend wyłączony.

Poprzednie wartości lądują w `%USERPROFILE%\.claude\ask_power_backup.json`; `99_uninstall.ps1`
przywraca je co do minuty.

### Krok 3. Zadania: most, watchdog, git pull (3 min, ten sam admin PowerShell)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\02_install_tasks.ps1
```

Zapyta o **hasło do twojego konta Windows**. To nie jest kaprys: zadanie uruchamiane „gdy użytkownik
zalogowany" umiera po restarcie na ekranie logowania. Z zapisanym hasłem most wstaje razem
z systemem, przed jakimkolwiek logowaniem. Konto musi być twoje, a nie SYSTEM, bo `claude`
czyta logowanie z `%USERPROFILE%\.claude`.

Powstają trzy zadania w folderze `\AskBridge\`:

| zadanie | kiedy | co robi |
|---|---|---|
| `bridge` | przy starcie systemu | czeka na adres Tailscale (do 120 s), uruchamia `ask_server.py`, przy awarii restart 3× co minutę |
| `watchdog` | co 5 minut | `GET /health`; brak odpowiedzi → restart zadania `bridge` + powiadomienie |
| `gitpull` | co godzinę | `git pull --ff-only` w każdym repo; **pomija repo z brudnym drzewem** i nigdy nie pushuje |

Watchdog robi dodatkowo **głęboki test co godzinę** (`ASK_DEEP_MIN`): zadaje mostowi prawdziwe
pytanie i sprawdza, czy wróciła treść. To jedyny sposób, żeby wyłapać awarię, której `/health`
nie widzi — wygasłą sesję `claude`, czyli „serwer żyje, odpowiedzi puste".

Jeśli konto nie ma hasła: `.\02_install_tasks.ps1 -NoPassword` (wtedy most wstaje dopiero po
pierwszym zalogowaniu po restarcie).

### Krok 4. Skrót „Wyjście" (30 s, zwykły PowerShell)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install_shortcut.ps1
```

Na pulpicie pojawia się `Wyjscie` z globalnym skrótem **Ctrl+Alt+Q**: blokuje sesję i **natychmiast**
gasi monitory (nie czeka tych 5 minut). Nie kasuj skrótu z pulpitu — hotkey działa tylko dopóki on tam jest.

### Krok 5. Sprawdzenie na miejscu (2 min)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\check_bridge.ps1
```

Ma wypisać `health 200` i pełną odpowiedź z czasem. Zapisz ten czas — to pierwszy pomiar mostu
na maszynie docelowej i wchodzi do notatki sesji.

### Krok 6. Test tego, po co to wszystko (3 min)

1. `Ctrl+Alt+Q` — ekran gaśnie, komputer pracuje.
2. Z telefonu (ta sama sieć nie jest potrzebna, tailnet wystarczy) albo z drugiej maszyny:

   ```powershell
   .\check_bridge.ps1 -Address <tailscale-ip-peceta> -Secret <sekret>
   ```

3. **Restart peceta** i powtórz punkt 2 bez logowania się na niego. To jest właściwy test:
   most ma odpowiadać z ekranu logowania.
4. `powercfg /requests` po 10 minutach ciemnego ekranu — ma pokazywać, że nic nie usypia maszyny.

### Krok 7. Adres do skrótu na iPhonie

```
http://<tailscale-ip-peceta>:8787/ask/<sekret>
```

Reszta kroków skrótu jest w `notes/HANDOFF_most_pytan.md` i się nie zmienia.

---

## Co robisz codziennie, wychodząc z pracy

**Ctrl+Alt+Q.** Nic więcej. Nie wyłączaj komputera, nie wylogowuj się (wylogowanie nie zabije
mostu, bo zadanie ma zapisane hasło, ale zamknie twoje okna).

Czego **nie** robić: „Zamknij system", „Uśpij", wyłączanie listwy zasilającej, wyciąganie kabla
sieciowego. Monitor z żółtą diodą to stan poprawny.

---

## Gdy coś nie działa

| objaw | przyczyna, którą sprawdzić najpierw |
|---|---|
| most nie odpowiada po restarcie | `Get-ScheduledTaskInfo -TaskPath \AskBridge\ -TaskName bridge` — kod `0x41303` znaczy „nigdy nie uruchomione", `0x1` szukaj w `project_files\run_files\bridge_stdout.log` |
| odpowiedzi puste albo „error" | wygasła sesja `claude` — zaloguj się raz interaktywnie na tym koncie |
| `health` działa z peceta, nie z telefonu | `ASK_BIND` wskazuje inny adres niż `tailscale ip -4`, albo zapora blokuje port; most **celowo** nie słucha na `0.0.0.0` |
| serwer pada przy pierwszym nagraniu | `ctranslate2` w złej wersji — `pip install "ctranslate2==4.5.0"` |
| komputer jednak zasnął | `powercfg /requests` i `powercfg /lastwake`; sprawdź, czy BIOS nie ma własnego usypiania i czy plan zasilania nie wrócił do domyślnego |
| port zajęty po testach | zostawione instancje z sesji 2026-09-14 słuchały na 8793 i 8794 |
| trzeba się dostać zdalnie | Pulpit zdalny po Tailscale (`mstsc /v:<tailscale-ip>`); Tailscale SSH nie działa na serwerze Windows |

Logi, wszystkie poza repo (ZASADY 2.5), w `project_files\run_files\`:
`ask_server.log`, `bridge.log`, `bridge_stdout.log`, `watchdog.log`, `git_pull.log`.

## Wycofanie

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\99_uninstall.ps1
```

Kasuje trzy zadania i przywraca zasilanie z kopii. `-KeepPower` zostawia ustawienia zasilania.

## Gdy coś jest inaczej

- **Komputer w domenie firmowej** — zasady grupy potrafią nadpisać plan zasilania i wymusić
  restarty; `00_check.ps1` to wykryje i zgłosi. Wtedy zamiast `powercfg` trzeba pytać IT albo
  pogodzić się z restartami (most wstaje sam, więc restart boli tylko przez minutę).
- **Brak praw administratora** — odpada `01_power.ps1` i zadanie przy starcie systemu. Most da się
  uruchomić jako zadanie „przy logowaniu", a ekran gasić skrótem `Ctrl+Alt+Q`; komputer będzie
  zasypiał wedle polityki firmy i to ustawienie trzeba wyprosić.
- **Powiadomienia z HA** — wypełnij `HA_NOTIFY_URL` w pliku env (webhook HA), wtedy padnięcie mostu
  i pusta odpowiedź z głębokiego testu wchodzą na telefon zamiast do loga.
