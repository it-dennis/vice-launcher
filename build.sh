#!/usr/bin/env bash
# Retrokauz VICE Launcher - Build Script (Linux / macOS)
# Hinweis: Erzeugt ein natives Binary fuer das jeweilige Betriebssystem,
# keine Windows-EXE. Fuer eine Windows-EXE bitte build.bat verwenden.
set -e

echo ""
echo "============================================="
echo " Retrokauz VICE Launcher  -  Build (Unix)"
echo "============================================="
echo ""

# Python pruefen (python3 bevorzugt)
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "FEHLER: Python wurde nicht gefunden."
    echo "Bitte Python 3.11+ installieren: https://www.python.org/"
    exit 1
fi
echo "Gefunden: $($PYTHON --version)"

# Virtuelles Environment erstellen, falls noch nicht vorhanden
if [ ! -d "venv" ]; then
    echo ""
    echo "Erstelle virtuelles Environment..."
    $PYTHON -m venv venv
fi

# venv aktivieren
# shellcheck disable=SC1091
source venv/bin/activate

# Abhaengigkeiten installieren
echo ""
echo "Installiere Abhaengigkeiten (pillow, pyinstaller)..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# Build starten
echo ""
echo "Starte PyInstaller-Build..."
echo ""
pyinstaller retrokauz_launcher.spec --noconfirm

echo ""
echo "============================================="
echo " BUILD ERFOLGREICH"
echo " Binary liegt in: dist/"
echo "============================================="
echo ""
