@echo off
setlocal enabledelayedexpansion
title Retrokauz VICE Launcher - Build

echo.
echo =============================================
echo  Retrokauz VICE Launcher  -  Build (Windows)
echo =============================================
echo.

:: Python pruefen
python --version >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Python wurde nicht gefunden.
    echo Bitte Python 3.11 oder neuer installieren: https://www.python.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo Gefunden: %%v

:: Virtuelles Environment erstellen, falls noch nicht vorhanden
if not exist "venv\" (
    echo.
    echo Erstelle virtuelles Environment...
    python -m venv venv
    if errorlevel 1 (
        echo FEHLER: venv konnte nicht erstellt werden.
        pause
        exit /b 1
    )
)

:: venv aktivieren
call venv\Scripts\activate.bat

:: Abhaengigkeiten installieren
echo.
echo Installiere Abhaengigkeiten (pillow, pyinstaller)...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo FEHLER: Pakete konnten nicht installiert werden.
    pause
    exit /b 1
)

:: Build starten
echo.
echo Starte PyInstaller-Build...
echo.
pyinstaller retrokauz_launcher.spec --noconfirm

if errorlevel 1 (
    echo.
    echo FEHLER: Build fehlgeschlagen. Siehe Ausgabe oben.
    pause
    exit /b 1
)

echo.
echo =============================================
echo  BUILD ERFOLGREICH
echo  EXE:  dist\retrokauz_launcher.exe
echo =============================================
echo.
pause
