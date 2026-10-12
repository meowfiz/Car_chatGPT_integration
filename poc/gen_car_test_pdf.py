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
    pdf.cell(0, 10, t("Sciaga - test CarPlay w aucie"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    pdf.cell(0, 6, t("Zmiana openspec: carplay-okna-projektow. Data: 2026-10-12."),
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font(fam, "B", 12)
    pdf.cell(0, 8, t("Co masz zrobic:"), new_x="LMARGIN", new_y="NEXT")
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
