# HOWTO — Dodać nową komendę głosową do CarPlay

Przewodnik dla rozwijania zestawu w aucie. Pokazuje jak dołożyć kolejny intent HA i endpoint
bramki, krok po kroku. Przykład: dodajemy komendę **„Claude godzina"** (zwraca aktualny
czas serwera jako Głosowo).

## Zasady projektowania

- **Krótka fraza** — 2–3 słowa po „Claude". STT w CarPlay rozpoznaje króciej niż długo.
- **Odpowiedź Głosowo-friendly** — do 15 słów, bez list, bez „kropka", bez „myślnik".
- **Reuse istniejących helperów** — fuzzy match przez `okna.resolve`, token przez
  `_car_authorized`, log przez `log("car-NAZWA", ...)`.
- **Autoryzacja wszędzie** (poza test-audio/text) — `Authorization: Bearer`.

## Krok 1 — endpoint bramki

W `D:\claude_projekty\project_integration\tools\voice_gateway.py` dodaj metodę jako
`_car_<nazwa>(self)` przed `_car_dispatch`:

```python
def _car_godzina(self):
    """GET /api/car/godzina -- aktualny czas serwera."""
    if not self._car_authorized():
        return
    now = datetime.now()
    # Krotki tekst: 'godzina HH:MM'
    text = now.strftime("godzina %H:%M")
    log("car-godzina", "ok")
    self._send(200, json.dumps({
        "text": text,
        "outcome": "sent",
    }, ensure_ascii=False), "application/json; charset=utf-8")
```

Dodaj routing w `do_GET` (lub `do_POST` dla komend ze stanem):

```python
elif path == "/api/car/godzina":
    self._car_godzina()
```

## Krok 2 — test po stronie bramki

Restart i smoke:

```powershell
python D:\claude_projekty\project_integration\monitor\services.py --restart
# Smoke:
$env:PYTHONIOENCODING = "utf-8"; python -c @"
import urllib.request, ssl, json, sys
ctx = ssl._create_unverified_context()
with open(r'C:\Users\meow\.claude\car_tokens.json', 'r', encoding='utf-8-sig') as f:
    tok = json.load(f)['token']
r = urllib.request.Request('https://100.127.128.47:8788/api/car/godzina',
    headers={'Authorization': 'Bearer ' + tok})
sys.stdout.buffer.write(urllib.request.urlopen(r, context=ctx, timeout=5).read())
"@
```

Oczekiwane: `{"text": "godzina 00:52", "outcome": "sent"}`.

## Krok 3 — rest_command po stronie HA

W `D:\claude_projekty\HA\voice\rest_command_claude.yaml` dodaj:

```yaml
rest_command:
  claude_godzina:
    url: "{{ states('sensor.glosy_serwer_url') }}/api/car/godzina"
    method: GET
    headers:
      Authorization: !secret car_token_header
    timeout: 10
    verify_ssl: false
```

## Krok 4 — intent w HA

W `D:\claude_projekty\HA\voice\claude_intent.yaml` dodaj akcję:

```yaml
GodzinaClaude:
  async_action: true
  speech:
    text: "Już patrzę, chwilę."
  action:
    - action: rest_command.claude_godzina
      response_variable: odp
      continue_on_error: true
    - if:
        - condition: template
          value_template: "{{ odp is defined and odp.status == 200 and odp.content.text is defined }}"
      then:
        - action: script.zapowiedz
          data:
            tekst: "{{ odp.content.text }}"
      else:
        - action: script.zapowiedz
          data:
            tekst: "Zegar nie odpowiada."
```

## Krok 5 — frazy wyzwalające w HA

W `D:\claude_projekty\HA\voice\claude_sentences_pl.yaml` dodaj do sekcji `intents:`:

```yaml
  GodzinaClaude:
    data:
      - sentences:
          - "(claude|klod|klot|klon|klok|klaud) godzina"
          - "(claude|klod|klot|klon|klok|klaud) ktora godzina"
          - "(claude|klod|klot|klon|klok|klaud) ile jest"
```

**UWAGA**: STT w CarPlay różnie transkrybuje „Claude" — zawsze dodawaj wszystkie 6
wariantów `claude|klod|klot|klon|klok|klaud`.

## Krok 6 — reload HA

Z poziomu bramki:

```bash
cd D:\claude_projekty\HA
# Reload rest_command i intent_script i conversation
# (HA Claude okno to robi przez curl do /api/services/*reload)
```

Albo w HA UI: Settings → Server Controls → Reload → wybierz REST Commands /
Conversation / Intents.

## Krok 7 — test w kuchni (nie w aucie)

Telefon, HA Companion, otwórz dowolny dashboard, dotknij Assist, powiedz
„Claude godzina". Słyszysz twoim głosem „godzina HH:MM" przez głośnik telefonu.

Jeśli błąd — sprawdź log HA (`/config/home-assistant.log`), log bramki
(`voice_gateway.log` — szukaj `car-godzina` wpisu).

## Krok 8 — test w aucie

CarPlay USB, dotknij Home Assistant → Assist, powiedz tę samą frazę.
Jak zagra — gotowe.

## Krok 9 — self-test

Dodaj przypadek do `D:\claude_projekty\Car_chatGPT_integration\poc\car_selftest.py`:

```python
("car.godzina", "GET", "/api/car/godzina", None,
 lambda rc, body, dt: (
     rc == 200 and body.get("outcome") == "sent" and "godzina" in body.get("text", ""),
     "text: %s" % body.get("text", ""))),
```

Uruchom:
```powershell
python D:\claude_projekty\Car_chatGPT_integration\poc\car_selftest.py
# -> 16/16 PASS
```

## Krok 10 — dokumentacja

- Dopisz do tabeli w `notes/HANDOFF_car_endpoints.md` (sekcja na górze „Pełna tabela
  mapowania HA ↔ bramka"): `| GodzinaClaude | „Claude godzina" | GET /api/car/godzina |`.
- Dopisz do PDF ściągi (jeśli regenerujesz) w `poc/gen_car_test_pdf.py`.
- Dopisz do raportu/notatki sesji.

## Krok 11 — commit i push w obu repo

```bash
# project_integration
cd D:\claude_projekty\project_integration
git add tools/voice_gateway.py
git commit -m "feat(car): /api/car/godzina"
git push

# HA
cd D:\claude_projekty\HA
git add voice/claude_sentences_pl.yaml voice/claude_intent.yaml voice/rest_command_claude.yaml
git commit -m "feat(voice): GodzinaClaude intent"
git push

# Car_chatGPT_integration (dokumentacja + selftest)
cd D:\claude_projekty\Car_chatGPT_integration
git add notes/HANDOFF_car_endpoints.md poc/car_selftest.py
git commit -m "docs(car): dodane GodzinaClaude"
git push
```

## Checklist

- [ ] Endpoint działa (smoke test z komputera 200 OK)
- [ ] rest_command, intent, sentences dodane w HA
- [ ] HA reload wykonany
- [ ] Test w kuchni OK — twoim głosem Sznuka
- [ ] Test w aucie OK (albo zaplanowany)
- [ ] Self-test rozszerzony, PASS
- [ ] HANDOFF + PDF + raport zaktualizowane
- [ ] Commit i push w 3 repo

## Gdzie szukać gdy coś nie działa

- **STT nie łapie frazy** → sprawdź warianty w `claude_sentences_pl.yaml`; może brakuje
  `klok` albo `klolt`. Loguje się w `voice_gateway.log` przez `/voice/match`.
- **HA mówi „Nie rozumiem"** → intent nie dopasowany, STT dobry; sprawdź
  `conversation.process` log HA — co właściwie wpadło.
- **TTS brzmi Piperem, nie Sznukiem** → `script.zapowiedz` zepsute; sprawdź
  `scripts.yaml`, czy używa `tts.speak` z `tts.glosy_prywatne`.
- **turn_on wygrywa z intentem** → encja o tej samej nazwie co fraza; przemianuj
  encję w HA entity_registry.
- **401 bez wyraźnej przyczyny** → token w `secrets.yaml` HA różny od tego w
  `~/.claude/car_tokens.json`. Sprawdź oba.
- **Bramka cisza / timeout** → `monitor/services.py --restart`; voice gateway log
  da więcej.
