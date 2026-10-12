"""Generuje PDF ze sciaga do testow CarPlay (seria A/B/C).

Wywolanie:
    python poc/gen_car_test_pdf.py [--out <path>]

Czcionka: DejaVu Sans TTF, bo helvetica w fpdf2 nie ma polskich znakow. Font szukany w kilku
typowych lokalizacjach Windows i WSL; brak -> fallback do helvetica + deakcentuacji.
"""
from __future__ import annotations

import argparse
import os
from fpdf import FPDF


FONT_CANDIDATES = [
    r"C:\Windows\Fonts\DejaVuSans.ttf",
    r"C:\Windows\Fonts\dejavu-sans.ttf",
    r"C:\Windows\Fonts\Verdana.ttf",
    r"C:\Windows\Fonts\verdana.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\Arial.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def find_font() -> tuple[str | None, str | None]:
    """Zwraca (regular_path, bold_path) albo (None, None)."""
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            # Prostu heurystyka na bolda przy tej samej rodzinie
            dirn = os.path.dirname(p)
            base = os.path.splitext(os.path.basename(p))[0].lower()
            bold_candidates = [
                os.path.join(dirn, base + "bd.ttf"),
                os.path.join(dirn, base + "-bold.ttf"),
                os.path.join(dirn, "DejaVuSans-Bold.ttf"),
                os.path.join(dirn, "arialbd.ttf"),
                os.path.join(dirn, "Verdana Bold.ttf"),
                os.path.join(dirn, "verdanab.ttf"),
                os.path.join(dirn, "segoeuib.ttf"),
            ]
            bold = next((b for b in bold_candidates if os.path.exists(b)), None)
            return p, bold
    return None, None


def build_pdf(out_path: str) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    regular, bold = find_font()
    use_tt = regular is not None
    if use_tt:
        pdf.add_font("ui", "", regular)
        if bold:
            pdf.add_font("ui", "B", bold)
        else:
            pdf.add_font("ui", "B", regular)
        fam = "ui"
    else:
        fam = "helvetica"

    def t(s: str) -> str:
        if use_tt:
            return s
        # fallback: ascii-only
        repl = {
            0x0105: "a", 0x0107: "c", 0x0119: "e", 0x0142: "l",
            0x0144: "n", 0x00F3: "o", 0x015B: "s", 0x017C: "z", 0x017A: "z",
            0x0104: "A", 0x0106: "C", 0x0118: "E", 0x0141: "L",
            0x0143: "N", 0x00D3: "O", 0x015A: "S", 0x017B: "Z", 0x0179: "Z",
            0x2014: "-", 0x2013: "-", 0x201E: '"', 0x201D: '"', 0x2018: "'", 0x2019: "'",
            0x2026: "...",
        }
        return s.translate(repl)

    # Tytul
    pdf.set_font(fam, "B", 16)
    pdf.cell(0, 10, t("Sciaga - CarPlay v3 (komendy glosowe)"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.cell(0, 6, t("Zmiana openspec: carplay-okna-projektow. Data: 2026-10-12."),
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Status 2026-10-12
    pdf.set_font(fam, "B", 11)
    pdf.cell(0, 7, t("Status 2026-10-12:"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "TTS Twoim glosem Sznuk na wszystkich komendach (nie tylko ZapytajClaude),\n"
        "turn_on hijacking rozwiazany (encje input_boolean.pm_* przemianowane w\n"
        "entity_registry), 11 intentow HA aktywnych."
    ))
    pdf.ln(4)

    # ====================================================================
    # NOWA SEKCJA: komendy glosowe po zdanym PoC
    # ====================================================================
    pdf.set_font(fam, "B", 14)
    pdf.cell(0, 9, t("Komendy glosowe (po zdanym PoC)"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "PoC audio zdany: HA Assist przez CarPlay dowozi odpowiedz Twoim glosem (Sznuk).\n"
        "Ponizej wlasciwe komendy funkcjonalne pietra sterowania. Wszystkie zaczynaja sie\n"
        "od slowa 'Claude' (wake word parsera). Mowisz do HA Assist (ikona HA w CarPlay)."
    ))
    pdf.ln(2)

    # 1. Ping petli
    pdf.set_font(fam, "B", 11)
    pdf.cell(0, 7, t("1. Ping petli"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "Co mowisz: 'Claude test' / 'Claude ping' / 'Claude sprawdz'.\n"
        "Co uslyszysz: 'petla dziala'.\n"
        "Co testuje: cala sciezka telefon -> HA -> parser -> glos w aucie."
    ))
    pdf.ln(2)

    # 2. Menu
    pdf.set_font(fam, "B", 11)
    pdf.cell(0, 7, t("2. Menu glosowe"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "Co mowisz: 'Claude pomoc' / 'Claude menu' / 'Claude sciaga' / 'Claude help'.\n"
        "Co uslyszysz: recytacje listy projektow i form fraz, ktorych mozesz uzyc.\n"
        "Kiedy uzyc: nie pamietasz nazwy projektu albo skladni polecenia."
    ))
    pdf.ln(2)

    # 3. Status agregat
    pdf.set_font(fam, "B", 11)
    pdf.cell(0, 7, t("3. Status - agregat wszystkich projektow"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "Co mowisz: 'Claude status' / 'Claude stan' / 'Claude co slychac' / 'Claude raport'.\n"
        "Co uslyszysz: ile projektow, ile pracuje teraz, ile otwartych zadan,\n"
        "ile commitow niewypchnietych."
    ))
    pdf.ln(2)

    # 4. Otworz okno
    pdf.set_font(fam, "B", 11)
    pdf.cell(0, 7, t("4. Otworz okno projektu"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "Co mowisz: 'Claude otworz <projekt>' / 'Claude odpal <projekt>' /\n"
        "   'Claude uruchom <projekt>'.\n"
        "Co uslyszysz: 'okno <projekt> otwarte' albo 'okno <projekt> juz dziala'.\n"
        "Efekt: w tmux (cli_bridge) powstaje sesja Claude Code dla tego projektu."
    ))
    pdf.ln(2)

    # 5. Podsumowanie
    pdf.set_font(fam, "B", 11)
    pdf.cell(0, 7, t("5. Podsumowanie konkretnego projektu"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "Co mowisz: 'Claude podsumowanie <projekt>' / 'Claude co z <projekt>' /\n"
        "   'Claude jak idzie <projekt>' / 'Claude stan <projekt>'.\n"
        "Co uslyszysz: nad czym projekt pracuje, ile zadan zrobionych z ilu."
    ))
    pdf.ln(2)

    # 6. Do okna
    pdf.set_font(fam, "B", 11)
    pdf.cell(0, 7, t("6. Wyslij polecenie do okna projektu"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "Co mowisz: 'Claude do okna <projekt>, <polecenie>' /\n"
        "   'Claude w oknie <projekt>, <polecenie>'.\n"
        "Przyklady:\n"
        "   'Claude do okna car integration, pokaz tasks'\n"
        "   'Claude w oknie HA, co z sentences'\n"
        "Efekt: polecenie trafia do dzialajacego Claude Code w sesji tmux projektu."
    ))
    pdf.ln(2)

    # 7. Kontynuuj
    pdf.set_font(fam, "B", 11)
    pdf.cell(0, 7, t("7. Kontynuacja bez powtarzania nazwy (sticky, 10 min)"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "Co mowisz: 'Claude kontynuuj <polecenie>' / 'Claude dalej <polecenie>'.\n"
        "Efekt: polecenie leci do ostatnio uzywanego okna, jesli minelo < 10 min.\n"
        "Po 10 min musisz znow nazwac projekt ('Claude do okna X, ...')."
    ))
    pdf.ln(2)

    # 8. TODO
    pdf.set_font(fam, "B", 11)
    pdf.cell(0, 7, t("8. Zapisz zadanie / TODO"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "Co mowisz: 'Claude zapisz zadanie <tekst>' / 'Claude dodaj todo <tekst>' /\n"
        "   'Claude notatka <tekst>'.\n"
        "Efekt: wpis trafia do ~/.claude/carplay_todos.jsonl (data + tekst)."
    ))
    pdf.ln(2)

    # 9. Powtorz
    pdf.set_font(fam, "B", 11)
    pdf.cell(0, 7, t("9. Powtorz ostatnia odpowiedz"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "Co mowisz: 'Claude powtorz' / 'Claude jeszcze raz' / 'Claude nie slyszalem' /\n"
        "   'Claude co'.\n"
        "Co uslyszysz: ten sam tekst co ostatnio.\n"
        "Kiedy uzyc: podmuch w glosniku, halas, przeslyszanie."
    ))
    pdf.ln(2)

    # 10. Moje todo
    pdf.set_font(fam, "B", 11)
    pdf.cell(0, 7, t("10. Zobacz zapisane zadania"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "Co mowisz: 'Claude moje todo' / 'Claude ostatnie zadania' /\n"
        "   'Claude co mialem zrobic'.\n"
        "Co uslyszysz: recytacje 5 ostatnich TODO.\n"
        "Kiedy uzyc: przypomniec sobie co zapisales na petli lub w aucie."
    ))
    pdf.ln(2)

    # 11. Zamknij
    pdf.set_font(fam, "B", 11)
    pdf.cell(0, 7, t("11. Zakoncz sesje"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "Co mowisz: 'Claude zamknij' / 'Claude koniec' / 'Claude reset'.\n"
        "Co uslyszysz: 'zamkniete, bylo X' albo 'nie bylo aktywnej sesji'.\n"
        "Kiedy uzyc: zeby zmienic projekt bez czekania 10 min TTL."
    ))
    pdf.ln(2)

    # Nazwy projektow do wymowienia
    pdf.set_font(fam, "B", 12)
    pdf.cell(0, 8, t("Nazwy projektow latwe do wymowienia (wybor):"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "- 'car integration' (ten projekt)\n"
        "- 'project integration' (meta-projekt, spina wszystko)\n"
        "- 'HA' (dodatek Home Assistant)\n"
        "- 'publikacja' (artykul naukowy)\n"
        "- 'biometrix'\n"
        "- 'dashboard M'\n"
        "- 'VCC' (glos w aucie)\n"
        "Pelna lista 22 projektow -> powiedz 'Claude menu'."
    ))
    pdf.ln(2)

    # Oczekiwana forma odpowiedzi
    pdf.set_font(fam, "B", 12)
    pdf.cell(0, 8, t("Jak oceniac dzialanie:"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "- odpowiedz przychodzi Twoim glosem (Sznuk) przez glosnik auta\n"
        "- pelne zdanie, bez urywania\n"
        "- opoznienie do ~3 s przy pingu, do ~10 s przy komendach do okna\n"
        "- gdy parser nie zrozumie -> 'nie rozumiem, powiedz menu'"
    ))
    pdf.ln(6)

    # ====================================================================
    # HISTORIA: PoC serie A/B/C (zdane, zostaje jako diagnostyka)
    # ====================================================================
    pdf.set_font(fam, "B", 14)
    pdf.cell(0, 9, t("Historia PoC - serie A/B/C (zdane, diagnostyka)"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "Oryginalny protokol testu z pierwszej sesji. PoC zdany - HA Assist (seria C)\n"
        "dowozi odpowiedz Twoim glosem przez glosnik auta. Zostawione jako diagnostyka,\n"
        "gdy nowe komendy nie dzialaja: wraca sie tutaj zeby odciac warstwe (audio stack\n"
        "/ Shortcut / HA pipeline)."
    ))
    pdf.ln(2)

    pdf.set_font(fam, "B", 12)
    pdf.cell(0, 8, t("Jak odtworzyc PoC:"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "1. Auto na postoju, silnik na, telefon podpiety do CarPlay USB.\n"
        "2. Zrob trzy serie po 3 proby kazda (A, B, C).\n"
        "3. Przy kazdej probie zapisz: czy zagralo przez glosnik auta, pelne zdanie czy urwalo,\n"
        "   czy brzmialo twoim glosem czy systemowym Siri.\n"
        "4. Wracasz, mowisz: 'A: X z 3 OK, B: Y z 3 OK, C: Z z 3 OK, twoim glosem?'\n"
    ))
    pdf.ln(2)

    pdf.set_font(fam, "B", 12)
    pdf.cell(0, 8, t("Seria A - Siri Shortcut audio (kontrolka, moze urwac)"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        'Co mowisz: "Hej Siri, CarPlay audio test".\n'
        "Co powinno sie stac: VCC glos powie \"test glosu w aucie\" (ale pewnie urwie po 'test').\n"
        "Co jest testowane: czy Tailscale, cert i audio stack dotarly do CarPlay.\n"
        "3 proby, odstepy ~5 s."
    ))
    pdf.ln(2)

    pdf.set_font(fam, "B", 12)
    pdf.cell(0, 8, t("Seria B - Siri Shortcut tekst (ma dociagnac, glos Siri)"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        'Co mowisz: "Hej Siri, CarPlay text test".\n'
        'Co powinno sie stac: Siri (Zosia) przeczyta "test glosu w aucie" do konca.\n'
        "Co jest testowane: czy Shortcut potrafi dociagnac tekst (ale NIE twoim glosem).\n"
        "3 proby."
    ))
    pdf.ln(2)

    pdf.set_font(fam, "B", 12)
    pdf.cell(0, 8, t("Seria C - HA Assist (DOCELOWE, Twoj glos VCC)"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "Co klikasz: ikona Home Assistant w CarPlay -> kafelek Assist.\n"
        "Co mowisz (dowolna fraza polska, np.):\n"
        '   "test glosu w aucie"\n'
        '   "jaka godzina"\n'
        "Co powinno sie stac: Twoj glos (Sznuk) przez glosnik auta, pelne zdanie.\n"
        "Co jest testowane: cala petla HA pipeline PL + VCC + CarPlay audio.\n"
        "3 proby. TO JEST GLOWNY TEST."
    ))
    pdf.ln(2)

    pdf.set_font(fam, "B", 12)
    pdf.cell(0, 8, t("Co z tego wynika:"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "- C 3/3 pelne Twoim glosem -> OK, mozemy robic parser 'Claude, do okna X, Y'\n"
        "- C urywa albo milczy -> CarPlay odcina HA sesje audio, trzeba inaczej\n"
        "- A/B tylko diagnostyka, mozesz je pominac jesli C dziala\n"
    ))
    pdf.ln(2)

    pdf.set_font(fam, "B", 12)
    pdf.cell(0, 8, t("Teksty do uslyszenia (po polsku):"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.multi_cell(0, 6, t(
        "„test głosu w aucie”  (z polskim l)\n"
        "„jaka godzina”  (odpowie HA)\n"
        "Zrozumiale po polsku = da sie zrozumiec, prawdziwym glosem Sznuka"
    ))
    pdf.ln(4)

    pdf.set_font(fam, "", 9)
    pdf.multi_cell(0, 5, t(
        "Jak cokolwiek nie dziala, bramke mozna zrestartowac z komputera: "
        "python D:\\claude_projekty\\project_integration\\monitor\\services.py --restart"
    ))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    pdf.output(out_path)
    print("PDF: %s (%d bytes, font=%s)" %
          (out_path, os.path.getsize(out_path), fam))


def main():
    ap = argparse.ArgumentParser()
    default_out = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "project_files", "run_files", "car_test_sciaga.pdf",
    )
    ap.add_argument("--out", default=default_out)
    args = ap.parse_args()
    build_pdf(os.path.abspath(args.out))


if __name__ == "__main__":
    main()
