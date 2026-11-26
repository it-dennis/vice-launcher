<div align="center">

<img src="logo/by_retrokauz.png" alt="Retrokauz VICE Launcher Logo" width="300">

# 🕹️ Retrokauz VICE Launcher

**Ein schlankes GUI-Frontend für den [VICE-Emulator](https://vice-emu.sourceforge.io/) — einfach knorke Retro.**

![Platform](https://img.shields.io/badge/platform-Windows-0078D6?logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-GPLv3-blue)
![VICE](https://img.shields.io/badge/VICE-GPLv2%2B-8A2BE2)

</div>

---

VICE ist super! Und jetzt noch dieser Launcher dazu. Knorke und Retro. 💾

---

## 🎮 Unterstützte Emulatoren

| Button | Emulator | Executable |
|--------|----------|------------|
| X64sc | Commodore 64 (cycle-exakt) | `x64sc.exe` |
| C128 | Commodore 128 | `x128.exe` |
| VIC-20 | Commodore VIC-20 | `xvic.exe` |
| Plus/4 & C16 | Commodore Plus/4 & C16 | `xplus4.exe` |
| PET | Commodore PET | `xpet.exe` |
| C64 DTV | C64 Direct-to-TV | `x64dtv.exe` |
| SuperCPU64 | SuperCPU 64 | `xscpu64.exe` |
| CBM-II | CBM-II | `xcbm2.exe` |
| CBM-5x0 | CBM-5x0 | `xcbm5x0.exe` |

---

## ✨ Funktionen

- **Ein Klick, ein Emulator:** Jeder VICE-Emulator startet per Button. Optional lädt der Launcher dabei ein Disk-/Tape-/Programm-Image per Autostart.
- **Menü „Image“:**
  - *Neues Image erstellen und starten mit …* legt über `c1541` ein formatiertes Image an (d64, d71, d81, d80, d82, g64; je nach Emulator) und hängt es in Laufwerk 8 ein.
  - *Vorhandenes Image starten mit …* zeigt im Datei-Dialog nur die Endungen, die der gewählte Emulator lesen kann.
- **Image-Erkennung:** Passt Endung oder Startadresse des ersten Programms nicht zum gewählten Emulator, erscheint eine Warnung mit der Empfehlung, welcher Emulator geeignet ist.
- **Fenster-Layout:** Launcher und Emulatorfenster werden automatisch nebeneinander und mittig auf dem Monitor angeordnet.
- **C128:** Vor dem Start wählst du, ob nur das 40-Zeichen-Fenster (VIC-IIe) oder beide Bildschirme (40 und 80 Zeichen) geöffnet werden.
- **Menü „Info“:** zeigt den VICE-Pfad und einen Katalog aller Image-Formate. Der Katalog lässt sich als **PDF-Ratgeber** speichern (Endungen, Rechner, Zuordnung zu den Emulatoren, Tipps).
- **Menü „Einstellungen“:** Standardordner für Disk-Images festlegen oder zurücksetzen.

---

## ✅ Voraussetzungen

- **VICE** muss installiert sein → [Download vice-emu.sourceforge.io](https://vice-emu.sourceforge.io/)
- **Python 3.11+** (nur für den Quellstart / Build)
- **Pillow** (Bilder) und **reportlab** (PDF-Ratgeber) – beides über `pip install -r requirements.txt`

---

## 🚀 Schnellstart (Quellcode)

```bash
# 1. Repository klonen
git clone https://github.com/it-dennis/VICE-Launcher.git
cd VICE-Launcher

# 2. Virtuelle Umgebung erstellen und aktivieren
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux / macOS

# 3. Abhängigkeiten installieren
pip install -r requirements.txt

# 4. Launcher starten
python retrokauz_launcher.py
```

Beim ersten Start wird VICE automatisch gesucht. Wird es nicht gefunden, öffnet sich ein Dialog zum Auswählen des `bin`-Ordners. Der Pfad wird dauerhaft gespeichert (unter `%APPDATA%\retrokauz\vice-launcher\config.json`).

---

## 📦 EXE bauen (Windows)

```bat
build.bat
```

Die fertige EXE liegt danach unter `dist\retrokauz_launcher.exe` und kann ohne Python-Installation weitergegeben werden. Logo, Icons und Themes werden automatisch eingebettet.

---

## 🎨 Themes

Im Ordner `themes/` befinden sich QSS-Stildateien (C64-Look, Pixel-Style). Die Themes werden zur Laufzeit geladen und können jederzeit angepasst werden.

---

## 📁 Projektstruktur

```ini
VICE-Launcher/
├── retrokauz_launcher.py   # Hauptprogramm
├── image_guide_pdf.py      # PDF-Ratgeber „Image-Formate und Systeme“
├── retrokauz_launcher.spec # PyInstaller-Konfiguration
├── requirements.txt
├── build.bat               # Windows-Build-Skript
├── build.sh                # Linux/macOS-Build-Skript
├── icons/                  # Button-Icons
├── logo/                   # Logo-Grafiken (inkl. PDF-Header)
├── favicon/                # Fenster-Icon
├── themes/                 # QSS-Themes + Token-Datei
└── landingpage/            # Statische Projektseite (HTML)
```

---

## 📜 Lizenz

GNU GPL v3 – siehe [LICENSE](LICENSE).

VICE selbst steht unter der **GNU GPL v2+** und wird vom VICE-Team entwickelt.
Dieses Projekt ist kein offizielles VICE-Produkt und steht in keiner Verbindung zum VICE-Team.

---

<div align="center">

*Erstellt von [Dennis Rapp (Retrokauz)](https://dennisrapp.com)* 🖥️

</div>
