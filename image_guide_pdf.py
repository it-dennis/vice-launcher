"""
Retrokauz - VICE Launcher
Erzeugt den PDF-Ratgeber "Image-Formate & Systeme" (Menü Info -> Image-Formate).

Die Emulator-Tabelle und die Kurzbeschreibungen der Endungen kommen aus
retrokauz_launcher.py, damit PDF, Katalog und Datei-Dialoge nie auseinanderlaufen.
Alle Texte nutzen nur Zeichen aus WinAnsi (Standard-Schrift Helvetica).

Abhaengigkeit:
    pip install reportlab
"""

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BLUE      = colors.HexColor("#27188e")
BLUE_LITE = colors.HexColor("#766ad5")
ROW_ALT   = colors.HexColor("#eeedfa")
GRID      = colors.HexColor("#c9c5ee")

EMAIL = "info@retrokauz.de"
WEB   = "www.retrokauz.de"

# Technische Details je Endung: (Medium, Kapazitaet / Aufbau, Erklärung)
FORMAT_DETAILS = {
    "d64": ("Diskette 5,25 Zoll, Laufwerk 1541/1551",
            "35 Tracks, 683 Blöcke, 174.848 Byte (664 Blöcke frei)",
            "Das häufigste Format überhaupt. Eine 40-Track-Variante (196.608 Byte) "
            "wird von manchen Programmen und Laufwerks-Erweiterungen genutzt. Sichert nur "
            "die Dateien, keinen Kopierschutz."),
    "d67": ("Diskette 5,25 Zoll, Laufwerk 2040/3040",
            "35 Tracks, ca. 170 KB",
            "Älteres IEEE-488-Format der ersten Commodore-Doppellaufwerke (DOS 1). "
            "Wird fast nur im PET-Umfeld verwendet."),
    "d71": ("Diskette 5,25 Zoll, Laufwerk 1571",
            "70 Tracks (doppelseitig), 1366 Blöcke, 349.696 Byte",
            "Doppelseitiges Format des 1571, dem Laufwerk des C128. Im 1541-Modus des "
            "Laufwerks ist es zu d64 kompatibel."),
    "d80": ("Diskette 5,25 Zoll, Laufwerk 8050",
            "77 Tracks, 2083 Blöcke, 533.248 Byte",
            "Große Disketten der CBM-Bürorechner (PET/CBM 8000, CBM-II). "
            "Ca. 500 KB bei einseitiger Aufzeichnung."),
    "d81": ("Diskette 3,5 Zoll, Laufwerk 1581",
            "80 Tracks, 3200 Blöcke, 819.200 Byte (3160 Blöcke frei)",
            "Das größte gängige Format für C64 und C128. Unterstützt Unterverzeichnisse "
            "(Partitionen) und ist deshalb bei neuen Projekten beliebt."),
    "d82": ("Diskette 5,25 Zoll, Laufwerk 8250",
            "154 Tracks (doppelseitig), 4166 Blöcke, 1.066.496 Byte",
            "Doppelseitiges Gegenstück zum d80, ca. 1 MB. für PET/CBM und CBM-II."),
    "d90": ("Festplatte D9060/D9090",
            "5 bzw. 7,5 MB",
            "Abbild der Commodore-Festplatten für die IEEE-488-Rechner. Selten."),
    "g64": ("Diskette 5,25 Zoll, Laufwerk 1541 (Rohdaten)",
            "GCR-Bitstrom, Größe variabel (ca. 200-300 KB)",
            "Speichert die Spuren so, wie sie auf der Diskette magnetisiert sind, inklusive "
            "Kopierschutz, Fehlersektoren und Halbspuren. Wichtig für Original-Spiele "
            "mit Schutz."),
    "g71": ("Diskette 5,25 Zoll, Laufwerk 1571 (Rohdaten)",
            "GCR-Bitstrom, doppelseitig",
            "Wie g64, aber für doppelseitige 1571-Disketten."),
    "x64": ("Diskette 5,25 Zoll, Laufwerk 1541",
            "64-Byte-Kopf + d64-Daten",
            "Älteres Format des Emulators X64. VICE liest es, legt es aber nicht mehr neu "
            "an. für neue Images bitte d64 verwenden."),
    "t64": ("Kassetten-Archiv (Container)",
            "Verzeichnis + beliebig viele Programme",
            "Stammt vom Emulator C64S. Fasst mehrere Programme einer Kassette in einer Datei "
            "zusammen. Die Programme liegen als Dateien vor, nicht als Tonsignal."),
    "tap": ("Datasette (Tonband-Signal)",
            "Folge von Impulslängen",
            "Originalgetreues Abbild einer Kassette, auch mit Turbo-Ladern. Lädt so langsam "
            "wie das Original (außer VICE-Warp-Modus ist aktiv)."),
    "prg": ("Einzelnes Programm",
            "2 Byte Startadresse + Programmdaten",
            "Die einfachste Form: ein Programm in einer Datei. Die ersten zwei Byte nennen "
            "die Ladeadresse und verraten, für welchen Rechner es gebaut wurde."),
    "p00": ("Einzelnes Programm im PC64-Container",
            "26 Byte Kopf (\"C64File\") + PRG-Daten",
            "Behält den Original-Dateinamen (bis zu 16 Zeichen) bei. Verwandt sind s00 "
            "(Sequentiell), u00 (User) und r00 (Relativ)."),
    "crt": ("Steckmodul (Cartridge)",
            "Kopf (\"C64 CARTRIDGE\") + ROM-Blöcke",
            "Abbild eines Moduls mit Spiel, Utility oder Speichererweiterung. Der Kopf "
            "enthält den Modultyp, damit der Emulator es richtig einblendet."),
}

# Hintergrund je Emulator: Rechner, Jahr, Technik, Hinweise
SYSTEM_DETAILS = {
    "x64sc.exe": (
        "Commodore 64 (1982)",
        "CPU 6510 (ca. 1 MHz), 64 KB RAM, Grafikchip VIC-II, Soundchip SID 6581/8580. "
        "BASIC V2 beginnt bei $0801. Der meistverkaufte Heimcomputer seiner Zeit. "
        "X64sc ist die zyklusgenaue \"Software-Cycle\"-Variante und die empfohlene Wahl "
        "für Spiele und Demos.",
    ),
    "x128.exe": (
        "Commodore 128 (1985)",
        "CPU 8502 (1 oder 2 MHz) plus Z80 für CP/M, 128 KB RAM, VIC-IIe und VDC für "
        "80 Zeichen. BASIC 7.0 beginnt bei $1C01. Startet wahlweise im C128-, C64- oder "
        "CP/M-Modus. Programme im C64-Modus brauchen eine C64-Startadresse ($0801), "
        "werden vom Autostart aber im C128-Modus geladen - dafür ist X64sc besser.",
    ),
    "xvic.exe": (
        "VIC-20 (1981)",
        "CPU 6502 (ca. 1 MHz), 5 KB RAM (3,5 KB frei für BASIC), Chip VIC. "
        "Die Startadresse hängt vom Speicherausbau ab: $1001 unerweitert, $0401 mit "
        "3-KB-Erweiterung, $1201 mit 8 KB oder mehr. Programme für den VIC-20 laufen "
        "nicht auf dem C64.",
    ),
    "xplus4.exe": (
        "Commodore Plus/4 und C16/C116 (1984)",
        "CPU 7501/8501, 64 KB (C16: 16 KB), Chip TED, eingebautes Office-Paket beim "
        "Plus/4. BASIC 3.5 beginnt bei $1001 - dieselbe Adresse wie beim unerweiterten "
        "VIC-20, deshalb kann der Launcher beide nicht allein über die Adresse "
        "unterscheiden.",
    ),
    "xpet.exe": (
        "Commodore PET 2001 und CBM 3000/4000/8000 (ab 1977)",
        "CPU 6502, 4 bis 96 KB RAM, Textbildschirm mit 40 oder 80 Spalten, "
        "BASIC 1/2/4 beginnt bei $0401. Laufwerke hängen am IEEE-488-Bus "
        "(2040, 4040, 8050, 8250), deshalb sind d80 und d82 hier üblich.",
    ),
    "x64dtv.exe": (
        "Direct-to-TV (2004)",
        "Das \"Direct-to-TV\"-Joystick-Geraet nach Jeri Ellsworth: ein C64 in einem Chip "
        "mit verbessertem Grafikchip und mehr Farben. Hat kein Diskettenlaufwerk und keine "
        "Kassette, daher passen vor allem prg, p00 und d64-Images mit prg-Dateien.",
    ),
    "xscpu64.exe": (
        "Turbokarte für den C64 (1996)",
        "Beschleunigerkarte von CMD für den C64 mit 65816-Prozessor und 20 MHz. "
        "Arbeitet mit allen C64-Images, hält aber manche zeitkritischen Spiele nicht "
        "aus. Gleiche Startadresse wie der C64 ($0801).",
    ),
    "xcbm2.exe": (
        "Serie B und P (CBM 600/700, 1983)",
        "CPU 6509 mit Speicherbanking, Textbildschirm (600/700) und BASIC 4.0. "
        "Programme liegen in Bank 1 und beginnen bei $0003. Laufwerke wie beim PET "
        "(IEEE-488), daher d80/d82.",
    ),
    "xcbm5x0.exe": (
        "Serie P (CBM 500, 1983)",
        "Wie CBM-II, aber mit dem Grafikchip VIC-II (wie im C64) statt eines "
        "Textbildschirms. Seltener Rechner, gleiche Image-Typen wie der CBM-II.",
    ),
}

# Startadresse -> Rechner (wie in der Image-Erkennung des Launchers)
LOAD_ADDRESSES = [
    ("$0801", "C64, C64 DTV, SuperCPU64"),
    ("$1C01", "C128"),
    ("$1001", "VIC-20 (unerweitert) oder Plus/4 / C16"),
    ("$1201", "VIC-20 (8 KB oder mehr)"),
    ("$0401", "PET / CBM 3000-8000 oder VIC-20 mit 3 KB"),
    ("$0003", "CBM-II und CBM-5x0"),
]


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=base["Title"], textColor=BLUE, fontSize=22,
                                leading=26, spaceAfter=2),
        "sub":   ParagraphStyle("s", parent=base["Normal"], textColor=BLUE_LITE, fontSize=11,
                                spaceAfter=10),
        "h1":    ParagraphStyle("h1", parent=base["Heading1"], textColor=BLUE, fontSize=15,
                                spaceBefore=14, spaceAfter=6, keepWithNext=1),
        "h2":    ParagraphStyle("h2", parent=base["Heading2"], textColor=BLUE, fontSize=11.5,
                                spaceBefore=8, spaceAfter=3, keepWithNext=1),
        "body":  ParagraphStyle("b", parent=base["BodyText"], fontSize=9.5, leading=13.5),
        "cell":  ParagraphStyle("c", parent=base["BodyText"], fontSize=8.3, leading=10.5),
        "cellb": ParagraphStyle("cb", parent=base["BodyText"], fontSize=8.3, leading=10.5,
                                fontName="Helvetica-Bold"),
        "head":  ParagraphStyle("hd", parent=base["BodyText"], fontSize=8.3, leading=10.5,
                                fontName="Helvetica-Bold", textColor=colors.white),
        "mid":   ParagraphStyle("m", parent=base["BodyText"], fontSize=8.5, leading=10.5,
                                alignment=TA_CENTER),
    }


def _table(data, col_widths, align_center_from: int | None = None) -> Table:
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
    ]
    if align_center_from is not None:
        style.append(("VALIGN", (align_center_from, 1), (-1, -1), "MIDDLE"))
    t.setStyle(TableStyle(style))
    return t


def _footer(canvas, doc) -> None:
    """Fusszeile auf jeder Seite: Mail, Webseite (klickbar) und Seitenzahl."""
    canvas.saveState()
    w, _ = A4
    canvas.setStrokeColor(BLUE)
    canvas.setLineWidth(0.8)
    canvas.line(18 * mm, 15 * mm, w - 18 * mm, 15 * mm)
    canvas.setFont("Helvetica", 8.5)
    canvas.setFillColor(BLUE)
    mail_w = canvas.stringWidth(EMAIL, "Helvetica", 8.5)
    canvas.drawString(18 * mm, 10 * mm, EMAIL)
    canvas.linkURL(f"mailto:{EMAIL}", (18 * mm, 9 * mm, 18 * mm + mail_w, 13 * mm))
    sep_x = 18 * mm + mail_w
    canvas.setFillColor(colors.grey)
    canvas.drawString(sep_x, 10 * mm, "   |   ")
    web_x = sep_x + canvas.stringWidth("   |   ", "Helvetica", 8.5)
    web_w = canvas.stringWidth(WEB, "Helvetica", 8.5)
    canvas.setFillColor(BLUE)
    canvas.drawString(web_x, 10 * mm, WEB)
    canvas.linkURL(f"https://{WEB}", (web_x, 9 * mm, web_x + web_w, 13 * mm))
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(w - 18 * mm, 10 * mm, f"Retrokauz VICE Launcher  -  Seite {doc.page}")
    canvas.restoreState()


def create_format_pdf(path: Path, emulators: list[dict], format_info: dict[str, str],
                      logo_path: Path | None) -> None:
    """Schreibt den Ratgeber als PDF nach `path`. Wirft OSError, wenn nicht schreibbar."""
    st = _styles()
    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=22 * mm,
        title="Image-Formate und Systeme - Retrokauz VICE Launcher",
        author="Retrokauz", subject="Disk-, Tape- und Programm-Images für VICE",
    )
    avail = A4[0] - 36 * mm
    story: list = []

    # --- Kopf mit Logo ---
    if logo_path is not None and logo_path.is_file():
        logo_w = 80 * mm
        img_w, img_h = ImageReader(str(logo_path)).getSize()
        story.append(Image(str(logo_path), width=logo_w, height=logo_w * img_h / img_w, hAlign="CENTER"))
        story.append(Spacer(1, 6))
    story.append(Paragraph("Image-Formate und Systeme", st["title"]))
    story.append(Paragraph(
        f"Ratgeber zum VICE Launcher &nbsp;|&nbsp; Stand {date.today().strftime('%d.%m.%Y')}",
        st["sub"]))
    story.append(Paragraph(
        "VICE ist ein Emulator-Paket für die 8-Bit-Rechner von Commodore. Programme "
        "und Spiele liegen heute meist als <b>Image</b> vor: eine einzelne Datei, die den "
        "Inhalt einer Diskette, einer Kassette, eines Moduls oder eines einzelnen Programms "
        "enthält. Die <b>Endung</b> verrät das Format, aber nicht automatisch den Rechner. "
        "Dieser Ratgeber erklärt die Endungen, die Rechner dahinter und welcher Emulator im "
        "Launcher wozu passt.", st["body"]))

    # --- Endungen ---
    story.append(Paragraph("1. Die Endungen im Überblick", st["h1"]))
    rows = [[Paragraph(h, st["head"]) for h in ("Endung", "Medium", "Aufbau / Größe", "Erklärung")]]
    for ext, (medium, size, text) in FORMAT_DETAILS.items():
        rows.append([
            Paragraph(f".{ext}", st["cellb"]),
            Paragraph(medium, st["cell"]),
            Paragraph(size, st["cell"]),
            Paragraph(text, st["cell"]),
        ])
    story.append(_table(rows, [15 * mm, 36 * mm, 36 * mm, avail - 87 * mm]))

    # --- Systeme ---
    story.append(Paragraph("2. Die Rechner hinter den Emulatoren", st["h1"]))
    story.append(Paragraph(
        "Jeder Button im Launcher startet einen eigenen Emulator. Die Rechner sind "
        "untereinander nicht kompatibel - ein Programm für den VIC-20 läuft nicht auf dem "
        "C64, auch wenn beide die Endung .d64 oder .prg benutzen.", st["body"]))
    for emu in emulators:
        title, text = SYSTEM_DETAILS.get(emu["exe"], (emu["label"], ""))
        story.append(KeepTogether([
            Paragraph(f"{emu['label']} &nbsp;-&nbsp; {title}", st["h2"]),
            Paragraph(text, st["body"]),
            Paragraph(
                "<b>Öffnet:</b> " + ", ".join(f".{e}" for e in emu["open"]) + "<br/>"
                "<b>Neu anlegbar:</b> " + ", ".join(f".{e}" for e in emu["new"]),
                st["cell"]),
        ]))

    # --- Matrix ---
    story.append(Paragraph("3. Welche Endung passt zu welchem Emulator?", st["h1"]))
    story.append(Paragraph(
        "<b>+</b> = kann geöffnet und im Launcher neu angelegt werden &nbsp;&nbsp; "
        "<b>&bull;</b> = kann geöffnet werden &nbsp;&nbsp; leer = nicht unterstützt", st["body"]))
    story.append(Spacer(1, 4))
    head = [Paragraph("Endung", st["head"])] + [Paragraph(e["label"], st["head"]) for e in emulators]
    matrix = [head]
    for ext in format_info:
        row = [Paragraph(f".{ext}", st["cellb"])]
        for emu in emulators:
            if ext in emu["new"]:
                mark = "+"
            elif ext in emu["open"]:
                mark = "&bull;"
            else:
                mark = ""
            row.append(Paragraph(mark, st["mid"]))
        matrix.append(row)
    first = 16 * mm
    story.append(_table(matrix, [first] + [(avail - first) / len(emulators)] * len(emulators),
                        align_center_from=1))

    # --- Erkennung ---
    story.append(Paragraph("4. Wie der Launcher das passende System erkennt", st["h1"]))
    story.append(Paragraph(
        "Eine Diskette sagt nicht, für welchen Rechner sie gebaut wurde. Der Launcher liest "
        "deshalb vor dem Start die <b>Startadresse</b> des ersten Programms im Image. Jeder "
        "Rechner legt BASIC-Programme an einer anderen Stelle im Speicher ab:", st["body"]))
    story.append(Spacer(1, 4))
    addr_rows = [[Paragraph("Startadresse", st["head"]), Paragraph("Passender Rechner", st["head"])]]
    addr_rows += [[Paragraph(a, st["cellb"]), Paragraph(t, st["cell"])] for a, t in LOAD_ADDRESSES]
    story.append(_table(addr_rows, [28 * mm, avail - 28 * mm]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Passt der gewaehlte Emulator nicht, erscheint eine Warnung mit der Empfehlung. "
        "Bei Sammel-Disks, deren erstes Programm kein BASIC-Start ist, sowie bei g64, x64, "
        "tap und crt ist keine Erkennung möglich - dann startet das Image ohne Warnung.",
        st["body"]))

    # --- Tipps ---
    story.append(Paragraph("5. Praktische Tipps", st["h1"]))
    tips = [
        "<b>Neues Image:</b> Menü Image &gt; Neues Image erstellen. Der Disk-Name darf "
        "16 Zeichen haben, die ID zwei. Das Image wird über das VICE-Programm c1541 "
        "formatiert und im Laufwerk 8 eingehängt.",
        "<b>Verzeichnis ansehen:</b> Im Emulator <font face='Courier'>LOAD\"$\",8</font> "
        "und danach <font face='Courier'>LIST</font> zeigt den Inhalt der Diskette.",
        "<b>Programm laden:</b> <font face='Courier'>LOAD\"NAME\",8</font> (C64: mit "
        "<font face='Courier'>,8,1</font> für Programme, die an ihrer eigenen Adresse "
        "liegen), dann <font face='Courier'>RUN</font>.",
        "<b>Autostart:</b> Vorhandene Images lädt der Launcher per Autostart, das Programm "
        "startet also selbstständig. Leere, neue Images werden nur eingehängt.",
        "<b>Format wählen:</b> d64 ist für fast alles richtig. d81 bietet viel Platz für "
        "C64/C128, d80/d82 sind für PET und CBM-II gedacht, g64 nur für Kopierschutz.",
    ]
    for t in tips:
        story.append(Paragraph(t, ParagraphStyle("li", parent=st["body"], leftIndent=10,
                                                 bulletIndent=0, spaceAfter=3), bulletText="•"))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "VICE (Versatile Commodore Emulator) wird vom VICE-Team entwickelt und steht unter der "
        "GNU General Public License. Mehr unter https://vice-emu.sourceforge.io/",
        ParagraphStyle("note", parent=st["cell"], textColor=colors.grey)))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
