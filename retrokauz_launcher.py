"""
Retrokauz - VICE Launcher
Kleines Start-Fenster, das die einzelnen VICE-Emulatoren per Klick startet.

Der VICE-Ordner wird automatisch gesucht; falls nicht gefunden, fragt der
Launcher beim ersten Start danach und merkt sich die Auswahl dauerhaft
(siehe resolve_vice_bin / CONFIG_PATH). Logo, Favicon und Icons liegen im
Programmordner und werden ueber relative Pfade geladen - der Launcher
laesst sich daher 1:1 kopieren/weitergeben.

Anpassen:
    - PLACEHOLDER_ICON: Fallback-Icon, wenn ein spezifisches Icon fehlt
    - ICON_SIZE: Zielgroesse, auf die alle Button-Icons skaliert werden
    - LOGO_SIZE: Zielgroesse fuer das Logo
    - EMULATORS: Liste der Buttons (Label, Executable, Icon, optionale Args)

Abhaengigkeit:
    pip install pillow
"""

import ctypes
import ctypes.wintypes
import json
import os
import subprocess
import sys
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox


def _warn(msg: str) -> None:
    """Schreibt eine Warnung nach stderr – sicher auch in PyInstaller-EXEs ohne Konsole."""
    if sys.stderr is not None:
        sys.stderr.write(msg)


try:
    from PIL import Image, ImageTk
except ImportError:
    _warn(
        "Fehler: Pillow ist nicht installiert.\n"
        "Bitte installieren mit:  pip install pillow\n"
    )
    sys.exit(1)

# --------------------------------------------------------------------
# KONFIGURATION - hier alles anpassen
# --------------------------------------------------------------------
# Alle Pfade unten sind relativ zum Programmordner, damit der Launcher
# sich 1:1 weitergeben laesst (kopieren/zippen reicht, keine Anpassung
# noetig). Nur der VICE-Ordner wird automatisch gesucht bzw. beim
# ersten Start abgefragt, siehe resolve_vice_bin().
if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys._MEIPASS)
else:
    APP_DIR = Path(__file__).resolve().parent

# Ordner mit den Button-Icons (liegt im Programmordner und wird mitgeliefert).
ICON_DIR = APP_DIR / "icons"

# Vollstaendiger Pfad zum Logo. Auf None setzen, wenn kein Logo gewuenscht.
LOGO_PATH = APP_DIR / "logo" / "by_retrokauz.png"

# Header-Bild fuer den PDF-Ratgeber (nur dort verwendet).
PDF_HEADER_PATH = APP_DIR / "logo" / "PDF-Header.png"

# Vollstaendiger Pfad zum Favicon.
FAVICON_PATH = APP_DIR / "favicon" / "favicon.ico"

# Wird automatisch geladen, wenn das spezifische Icon eines Emulators fehlt.
# Auf None setzen, falls kein Fallback gewuenscht ist.
PLACEHOLDER_ICON = "placeholder_logo.png"

# Disk-Formate, die c1541 neu anlegen kann (je Emulator eine Teilmenge)
_NEW_C64  = ["d64", "d71", "d81", "d80", "d82", "g64"]
_NEW_PET  = ["d64", "d80", "d82"]
# Dateiendungen, die der jeweilige Emulator oeffnen/autostarten kann
_OPEN_DISK = ["d64", "d67", "d71", "d80", "d81", "d82", "d90", "g64", "g71", "x64"]
_OPEN_C64  = _OPEN_DISK + ["t64", "prg", "p00", "tap", "crt"]
_OPEN_DTV  = _OPEN_DISK + ["t64", "prg", "p00"]
_OPEN_VIC  = _OPEN_DISK + ["t64", "prg", "p00", "tap", "crt"]
_OPEN_PLUS = _OPEN_DISK + ["t64", "prg", "p00", "tap"]
_OPEN_PET  = ["d64", "d67", "d80", "d82", "d90", "prg", "p00", "tap"]

# Unterstuetzte Formate: PNG, JPG, JPEG, GIF, BMP, ICO, WEBP, TIFF
# args = optionale Kommandozeilen-Argumente pro Emulator, z.B. ["-fullscreen"]
# new  = Formate fuer "Neues Image erstellen", open = Endungen fuer "Image oeffnen"
_ICON = "vicelauncher_button.png"
EMULATORS = [
    {"label": "X64sc",        "exe": "x64sc.exe",   "icon": _ICON, "args": [], "new": _NEW_C64, "open": _OPEN_C64},
    {"label": "C128",         "exe": "x128.exe",    "icon": _ICON, "args": [], "new": _NEW_C64, "open": _OPEN_C64},
    {"label": "VIC-20",       "exe": "xvic.exe",    "icon": _ICON, "args": [], "new": _NEW_C64, "open": _OPEN_VIC},
    {"label": "Plus/4 & C16", "exe": "xplus4.exe",  "icon": _ICON, "args": [], "new": _NEW_C64, "open": _OPEN_PLUS},
    {"label": "PET",          "exe": "xpet.exe",    "icon": _ICON, "args": [], "new": _NEW_PET, "open": _OPEN_PET},
    {"label": "C64 DTV",      "exe": "x64dtv.exe",  "icon": _ICON, "args": [], "new": _NEW_C64, "open": _OPEN_DTV},
    {"label": "SuperCPU64",   "exe": "xscpu64.exe", "icon": _ICON, "args": [], "new": _NEW_C64, "open": _OPEN_C64},
    {"label": "CBM-II",       "exe": "xcbm2.exe",   "icon": _ICON, "args": [], "new": _NEW_PET, "open": _OPEN_PET},
    {"label": "CBM-5x0",      "exe": "xcbm5x0.exe", "icon": _ICON, "args": [], "new": _NEW_PET, "open": _OPEN_PET},
]

# Abstand zwischen Launcher- und Emulator-Fenster in Pixeln
WINDOW_GAP = 10

# Layout
COLUMNS = 3
ICON_SIZE = (80, 80)            # Zielgroesse fuer Button-Icons
LOGO_SIZE = (160, 60)           # Max. Zielgroesse fuer das Logo (Seitenverhaeltnis bleibt erhalten)
BTN_WIDTH = 150
BTN_HEIGHT_WITH_ICON = 140
BTN_HEIGHT_TEXT_ONLY = 70

# Farben (dunkles Theme)
BG_COLOR    = "#27188e"
BTN_COLOR   = "#27188e"
BTN_HOVER   = "#766ad5"
TEXT_COLOR  = "#f0f0f0"
MUTED_COLOR = "#aaaaaa"
DISK_BG     = "#221a7a"
FOOTER_BG   = "#1f1575"
LINK_COLOR  = "#8aacff"


# --------------------------------------------------------------------
# VICE-Ordner finden (Konfiguration + Auto-Erkennung + manuelle Auswahl)
# --------------------------------------------------------------------
# Eine Datei aus dem VICE-bin-Ordner, an der ein gueltiger Ordner erkannt wird.
VICE_MARKER_EXE = "x64sc.exe"

# Offizielle VICE-Downloadseite (wird angezeigt, wenn VICE nicht installiert ist).
# VICE wird vom VICE-Team entwickelt und steht unter der GNU GPL v2+.
# Weitere Infos: https://vice-emu.sourceforge.io/
VICE_DOWNLOAD_URL = "https://vice-emu.sourceforge.io/"

# Hier merkt sich der Launcher den einmal gewaehlten VICE-Pfad, damit man
# beim naechsten Start nicht erneut danach gefragt wird.
CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "retrokauz" / "vice-launcher"
CONFIG_PATH = CONFIG_DIR / "config.json"

# Ueblicherweise Orte, an denen ein VICE-Build landet. Wird der Reihe nach
# durchsucht, bis ein Ordner mit VICE_MARKER_EXE gefunden wird.
CANDIDATE_VICE_DIRS = [
    Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "VICE" / "bin",
    Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "VICE" / "bin",
    Path(os.environ.get("LOCALAPPDATA", Path.home())) / "VICE" / "bin",
    Path.home() / "Documents" / "Emulatoren" / "VICE" / "bin",
    Path.home() / "VICE" / "bin",
]


def _is_vice_bin(path: Path) -> bool:
    """Prueft, ob ein Ordner ein gueltiger VICE-bin-Ordner ist."""
    return path.is_dir() and (path / VICE_MARKER_EXE).is_file()


def load_config() -> dict:
    if CONFIG_PATH.is_file():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    return {}


def save_config(data: dict) -> None:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as e:
        _warn(f"Warnung: Konfiguration konnte nicht gespeichert werden: {e}\n")


def auto_detect_vice_bin() -> Path | None:
    """Sucht den VICE-bin-Ordner an den ueblichen Installationsorten."""
    for candidate in CANDIDATE_VICE_DIRS:
        if _is_vice_bin(candidate):
            return candidate
    return None


def ask_user_for_vice_bin(parent: tk.Tk | None = None) -> Path | None:
    """Fragt ob VICE installiert ist; oeffnet ggf. die Download-Seite.
    Sonst zeigt Ordnerauswahl-Dialog bis gueltiger Ordner gewaehlt wird."""
    already_installed = messagebox.askyesno(
        "VICE nicht gefunden",
        "Der VICE-Emulator wurde nicht automatisch gefunden.\n\n"
        "Ist VICE bereits auf diesem Computer installiert?\n\n"
        "Ja  → Installationsordner manuell auswaehlen\n"
        "Nein → VICE-Downloadseite im Browser oeffnen",
        parent=parent,
    )
    if not already_installed:
        webbrowser.open(VICE_DOWNLOAD_URL)
        messagebox.showinfo(
            "VICE herunterladen",
            "Die VICE-Downloadseite wurde im Browser geoeffnet.\n\n"
            "Nach der Installation kannst du diesen Launcher erneut starten.\n\n"
            f"VICE wird vom VICE-Team entwickelt (GNU GPL v2+).\n"
            f"Mehr Infos: {VICE_DOWNLOAD_URL}",
            parent=parent,
        )
        return None

    messagebox.showinfo(
        "VICE-Ordner waehlen",
        f"Bitte waehle den 'bin'-Ordner deiner VICE-Installation aus\n"
        f"(der Ordner, der z. B. '{VICE_MARKER_EXE}' enthaelt).",
        parent=parent,
    )
    while True:
        chosen = filedialog.askdirectory(title="VICE 'bin'-Ordner auswaehlen", parent=parent)
        if not chosen:
            return None
        chosen_path = Path(chosen)
        if _is_vice_bin(chosen_path):
            return chosen_path
        retry = messagebox.askretrycancel(
            "Ungueltiger Ordner",
            f"In diesem Ordner wurde keine '{VICE_MARKER_EXE}' gefunden:\n\n{chosen_path}\n\n"
            f"Bitte den 'bin'-Ordner deiner VICE-Installation auswaehlen.",
            parent=parent,
        )
        if not retry:
            return None


def resolve_vice_bin(parent: tk.Tk | None = None) -> Path | None:
    """Ermittelt den VICE-bin-Ordner: zuerst aus der gespeicherten
    Konfiguration, dann per Auto-Erkennung, zuletzt per Nachfrage beim
    Benutzer. Eine manuell gewaehlte Auswahl wird fuer naechste Starts
    gespeichert."""
    config = load_config()
    saved = config.get("vice_bin")
    if saved:
        saved_path = Path(saved)
        if _is_vice_bin(saved_path):
            return saved_path

    detected = auto_detect_vice_bin()
    if detected is not None:
        save_config({**config, "vice_bin": str(detected)})
        return detected

    chosen = ask_user_for_vice_bin(parent)
    if chosen is not None:
        save_config({**config, "vice_bin": str(chosen)})
    return chosen


# --------------------------------------------------------------------
# Emulator starten & Fenster positionieren
# --------------------------------------------------------------------

def _find_windows_for_pid(pid: int) -> list[int]:
    """Gibt die HWNDs aller sichtbaren Hauptfenster eines Prozesses zurueck."""
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_size_t, ctypes.c_size_t)
    user32 = ctypes.windll.user32
    found: list[int] = []

    def _cb(hwnd: int, _: int) -> bool:
        w_pid = ctypes.c_ulong(0)
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(w_pid))
        if (
            w_pid.value == pid
            and user32.IsWindowVisible(hwnd)
            and user32.GetWindowTextLengthW(hwnd) > 0
        ):
            found.append(hwnd)
        return True

    # cb muss in einer Variable gehalten werden; sonst sammelt der GC
    # den Zeiger ein, waehrend EnumWindows noch iteriert (Absturz).
    cb = EnumWindowsProc(_cb)
    user32.EnumWindows(cb, 0)
    return found


def _find_window_for_pid(pid: int) -> int | None:
    """Gibt das HWND des ersten sichtbaren Hauptfensters eines Prozesses zurueck."""
    found = _find_windows_for_pid(pid)
    return found[0] if found else None


class _MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize",    ctypes.c_ulong),
        ("rcMonitor", ctypes.wintypes.RECT),
        ("rcWork",    ctypes.wintypes.RECT),
        ("dwFlags",   ctypes.c_ulong),
    ]


def _monitor_info(hwnd: int) -> _MONITORINFO:
    """Liefert die Monitor-Infos (Gesamtflaeche und Arbeitsbereich) zum Fenster."""
    MONITOR_DEFAULTTONEAREST = 2
    hmon = ctypes.windll.user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
    mi = _MONITORINFO()
    mi.cbSize = ctypes.sizeof(_MONITORINFO)
    ctypes.windll.user32.GetMonitorInfoW(hmon, ctypes.byref(mi))
    return mi


def _is_window_fullscreen(hwnd: int) -> bool:
    """Prueft ob ein Fenster den gesamten Monitor belegt (Vollbild oder maximiert)."""
    win_rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(win_rect))
    m = _monitor_info(hwnd).rcMonitor
    return (
        win_rect.left <= m.left
        and win_rect.top <= m.top
        and win_rect.right >= m.right
        and win_rect.bottom >= m.bottom
    )


def _arrange_windows(root: tk.Tk, hwnd: int) -> None:
    """Stellt Launcher und Emulator(en) nebeneinander und zentriert die ganze Reihe
    im Arbeitsbereich des Monitors, auf dem der Launcher liegt. Hat der Emulator
    mehrere Fenster (x128: VIC-IIe + VDC), kommen alle in die Reihe."""
    user32 = ctypes.windll.user32
    if not user32.IsWindow(hwnd) or _is_window_fullscreen(hwnd):
        return

    pid = ctypes.c_ulong(0)
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    emu_hwnds = [hwnd] + [h for h in _find_windows_for_pid(pid.value) if h != hwnd]

    root.update_idletasks()
    launcher_hwnd = user32.GetParent(root.winfo_id())  # Tk-Toplevel-Rahmen
    row = [launcher_hwnd, *emu_hwnds]
    sizes = []
    for h in row:
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(h, ctypes.byref(rect))
        sizes.append((rect.right - rect.left, rect.bottom - rect.top))

    work = _monitor_info(launcher_hwnd).rcWork
    work_w, work_h = work.right - work.left, work.bottom - work.top
    total_w = sum(w for w, _ in sizes) + WINDOW_GAP * (len(row) - 1)

    SWP_NOSIZE     = 0x0001
    SWP_NOZORDER   = 0x0004
    SWP_NOACTIVATE = 0x0010
    flags = SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE

    x = work.left + max(0, (work_w - total_w) // 2)
    for h, (w, h_px) in zip(row, sizes):
        y = work.top + max(0, (work_h - h_px) // 2)
        user32.SetWindowPos(h, 0, x, y, 0, 0, flags)
        x += w + WINDOW_GAP


def _monitor_vice_window(root: tk.Tk, hwnd: int, was_fullscreen: bool) -> None:
    """Pollt das VICE-Fenster und positioniert es nach dem Verlassen des Vollbilds neu."""
    if not ctypes.windll.user32.IsWindow(hwnd):
        return  # VICE wurde geschlossen – Monitoring beenden

    is_fs = _is_window_fullscreen(hwnd)

    if was_fullscreen and not is_fs:
        # Kurze Pause, damit VICE die Fenster-Animation abschliessen kann
        root.after(200, lambda: _arrange_windows(root, hwnd))

    root.after(500, lambda: _monitor_vice_window(root, hwnd, is_fs))


def _poll_for_window(root: tk.Tk, pid: int, remaining: int, delay_ms: int = 250) -> None:
    """Pollt auf das Prozessfenster und positioniert es, sobald es erscheint."""
    hwnd = _find_window_for_pid(pid)
    if hwnd:
        _arrange_windows(root, hwnd)
        # VICE aendert die Fenstergroesse kurz nach dem Start noch -> nochmal zentrieren
        root.after(800, lambda: _arrange_windows(root, hwnd))
        root.after(2000, lambda: _arrange_windows(root, hwnd))
        # Monitoring starten: repositioniert VICE automatisch nach Vollbild-Exit
        root.after(500, lambda: _monitor_vice_window(root, hwnd, False))
        return
    if remaining > 1:
        root.after(delay_ms, lambda: _poll_for_window(root, pid, remaining - 1, delay_ms))


# --------------------------------------------------------------------
# Image-Erkennung: passt das Image zum gewaehlten Emulator?
# --------------------------------------------------------------------

# Startadresse des ersten Programms -> dazu passende Emulatoren (exe-Namen)
_ADDR_TO_EXES = {
    0x0801: ["x64sc.exe", "x64dtv.exe", "xscpu64.exe"],
    0x1C01: ["x128.exe"],
    0x1001: ["xvic.exe", "xplus4.exe"],
    0x1201: ["xvic.exe"],
    0x0401: ["xpet.exe", "xvic.exe"],
    0x0003: ["xcbm2.exe", "xcbm5x0.exe"],
}

# Ordner-Layout pro Disk-Format: (Verzeichnis-Track, Verzeichnis-Sektor, Sektoren pro Track)
def _sectors_per_track(fmt: str, track: int) -> int:
    if fmt in ("d64", "d71"):
        t = track if track <= 35 else track - 35
        return 21 if t <= 17 else 19 if t <= 24 else 18 if t <= 30 else 17
    if fmt == "d81":
        return 40
    t = track if track <= 77 else track - 77  # d80 / d82
    return 29 if t <= 39 else 27 if t <= 53 else 25 if t <= 64 else 23


def _read_sector(data: bytes, fmt: str, track: int, sector: int) -> bytes:
    index = sum(_sectors_per_track(fmt, t) for t in range(1, track)) + sector
    return data[index * 256:(index + 1) * 256]


def detect_load_address(path: Path) -> int | None:
    """Liest die Startadresse des ersten Programms im Image. None, wenn nicht erkennbar."""
    ext = path.suffix.lower().lstrip(".")
    try:
        data = path.read_bytes()
        if ext == "prg" and len(data) >= 2:
            return data[0] | data[1] << 8
        if ext == "p00" and len(data) >= 28:
            return data[26] | data[27] << 8
        if ext == "t64" and len(data) >= 0x44:
            return data[0x42] | data[0x43] << 8
        if ext in ("d64", "d71", "d81", "d80", "d82"):
            track, sector = {"d81": (40, 3), "d80": (39, 1), "d82": (39, 1)}.get(ext, (18, 1))
            for _ in range(40):  # Schutz vor Endlosschleifen bei defekten Images
                block = _read_sector(data, ext, track, sector)
                if len(block) < 256:
                    return None
                for pos in range(0, 256, 32):
                    ftype = block[pos + 2]
                    if ftype & 0x80 and ftype & 0x07 == 2:  # geschlossene PRG-Datei
                        first = _read_sector(data, ext, block[pos + 3], block[pos + 4])
                        return first[2] | first[3] << 8 if len(first) == 256 else None
                track, sector = block[0], block[1]
                if track == 0:
                    return None
    except (OSError, IndexError):
        pass
    return None


def check_image_compat(path: str, emu: dict) -> str | None:
    """Gibt einen Hinweistext zurueck, wenn das Image nicht zum Emulator passt, sonst None."""
    img = Path(path)
    ext = img.suffix.lower().lstrip(".")
    labels = {e["exe"]: e["label"] for e in EMULATORS}

    if ext in {x for e in EMULATORS for x in e["open"]} and ext not in emu["open"]:
        fits = [e["label"] for e in EMULATORS if ext in e["open"]]
        return (
            f"{emu['label']} kann Images vom Typ .{ext} nicht verarbeiten.\n\n"
            f"Dafür geeignet: {', '.join(fits)}"
        )

    addr = detect_load_address(img)
    fits_exes = _ADDR_TO_EXES.get(addr) if addr is not None else None
    if fits_exes and emu["exe"] not in fits_exes:
        return (
            f"Das Image '{img.name}' ist nach seiner Startadresse (${addr:04X}) "
            f"für einen anderen Rechner gedacht.\n\n"
            f"Empfohlen: {', '.join(labels[x] for x in fits_exes)}\n"
            f"Gewählt: {emu['label']}"
        )
    return None


def _ask_c128_display(parent: tk.Tk) -> str | None:
    """Fragt, welche Bildschirme der C128 zeigen soll: "both", "vic" oder None (Abbruch)."""
    win = tk.Toplevel(parent)
    win.title("C128 starten")
    win.configure(bg=BG_COLOR)
    win.resizable(False, False)
    result: list[str] = []

    tk.Label(
        win,
        text="Der C128 hat zwei Bildschirmausgänge.\nWelche sollen geöffnet werden?",
        font=("Segoe UI", 10),
        bg=BG_COLOR,
        fg=TEXT_COLOR,
        justify="left",
    ).pack(padx=20, pady=(16, 10))

    def _pick(choice: str) -> None:
        result.append(choice)
        win.destroy()

    for text, choice in (
        ("Beide (40 und 80 Zeichen)", "both"),
        ("Nur 40 Zeichen (VIC-IIe)", "vic"),
    ):
        tk.Button(
            win, text=text, command=lambda c=choice: _pick(c), bg=BTN_COLOR, fg=TEXT_COLOR,
            activebackground=BTN_HOVER, activeforeground=TEXT_COLOR,
            font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2", padx=10, pady=6,
        ).pack(fill="x", padx=20, pady=3)
    tk.Button(
        win, text="Abbrechen", command=win.destroy, bg=DISK_BG, fg=MUTED_COLOR,
        activebackground=BTN_HOVER, activeforeground=TEXT_COLOR,
        font=("Segoe UI", 9), relief="flat", cursor="hand2", padx=10, pady=4,
    ).pack(padx=20, pady=(8, 14))

    win.bind("<Escape>", lambda _e: win.destroy())
    _center_on_parent(win, parent)
    win.transient(parent)
    win.grab_set()
    win.focus_set()
    parent.wait_window(win)
    return result[0] if result else None


def launch_enhanced(
    root: tk.Tk,
    vice_bin: Path,
    exe_name: str,
    args: list[str],
    disk_image: str,
    attach_only: bool = False,
) -> None:
    """Startet den Emulator, laedt optional ein Disk-Image und positioniert das Fenster.
    attach_only=True haengt das Image nur in Laufwerk 8 ein (fuer leere, neue Images),
    sonst wird es per Autostart geladen und gestartet."""
    exe_path = vice_bin / exe_name
    if not exe_path.is_file():
        messagebox.showerror(
            "Datei nicht gefunden",
            f"Die Datei existiert nicht:\n\n{exe_path}\n\n"
            f"Bitte den VICE-Ordner pruefen "
            f"(Konfigurationsdatei: {CONFIG_PATH}).",
        )
        return

    if disk_image and not attach_only:
        emu = next((e for e in EMULATORS if e["exe"] == exe_name), None)
        hint = check_image_compat(disk_image, emu) if emu else None
        if hint and not messagebox.askyesno(
            "Image passt nicht zum Emulator",
            f"{hint}\n\nTrotzdem mit {emu['label']} starten?",
            default="no",
            parent=root,
        ):
            return

    if exe_name == "x128.exe":
        choice = _ask_c128_display(root)
        if choice is None:
            return
        # VICE speichert Kommandozeilen-Einstellungen; deshalb immer explizit setzen
        args = [*args, "+hidevdcwindow" if choice == "both" else "-hidevdcwindow"]

    cmd = [str(exe_path), *args]
    if disk_image:
        cmd += ["-8", disk_image] if attach_only else ["-autostart", disk_image]

    try:
        proc = subprocess.Popen(cmd, cwd=str(vice_bin))
        # Max. 5 Sekunden auf das VICE-Fenster warten (20 x 250 ms)
        _poll_for_window(root, proc.pid, remaining=20, delay_ms=250)
    except OSError as e:
        messagebox.showerror("Startfehler", f"{exe_name} konnte nicht gestartet werden:\n\n{e}")


# --------------------------------------------------------------------
# Neue Disk-Images anlegen (ueber c1541 aus dem VICE-Ordner)
# --------------------------------------------------------------------

def _center_on_parent(win: tk.Toplevel, parent: tk.Tk) -> None:
    """Zentriert ein Dialogfenster ueber dem Launcher, damit es direkt im Blick liegt."""
    win.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() - win.winfo_reqwidth()) // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - win.winfo_reqheight()) // 2
    win.geometry(f"+{max(0, x)}+{max(0, y)}")


def create_disk_image(vice_bin: Path, path: Path, name: str, disk_id: str, fmt: str) -> str | None:
    """Legt mit c1541 ein formatiertes Image an. Gibt eine Fehlermeldung zurueck, sonst None."""
    c1541 = vice_bin / "c1541.exe"
    if not c1541.is_file():
        return f"c1541.exe wurde im VICE-Ordner nicht gefunden:\n{c1541}"
    try:
        path.unlink(missing_ok=True)  # Ueberschreiben wurde im Speichern-Dialog bestaetigt
        result = subprocess.run(
            [str(c1541), "-format", f"{name},{disk_id}", fmt, str(path)],
            cwd=str(vice_bin),
            capture_output=True,
            text=True,
            timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError) as e:
        return str(e)
    if result.returncode != 0 or not path.is_file():
        return (result.stderr or result.stdout or "Unbekannter Fehler").strip()
    return None


def _ask_new_image(parent: tk.Tk, emu_label: str, formats: list[str]) -> tuple[str, str, str] | None:
    """Dialog fuer Disk-Name, Disk-ID und Format. Gibt (name, id, format) oder None zurueck."""
    win = tk.Toplevel(parent)
    win.title(f"Neues Image für {emu_label}")
    win.configure(bg=BG_COLOR)
    win.resizable(False, False)

    name_var = tk.StringVar(value="NEUES IMAGE")
    id_var   = tk.StringVar(value="00")
    fmt_var  = tk.StringVar(value=formats[0])
    result: list[tuple[str, str, str]] = []

    def _label(row: int, text: str) -> None:
        tk.Label(win, text=text, font=("Segoe UI", 9), bg=BG_COLOR, fg=TEXT_COLOR).grid(
            row=row, column=0, sticky="w", padx=(14, 6), pady=6
        )

    _label(0, "Disk-Name (max. 16 Zeichen):")
    tk.Entry(win, textvariable=name_var, width=22, font=("Segoe UI", 9)).grid(
        row=0, column=1, padx=(0, 14), pady=6
    )
    _label(1, "Disk-ID (max. 2 Zeichen):")
    tk.Entry(win, textvariable=id_var, width=5, font=("Segoe UI", 9)).grid(
        row=1, column=1, sticky="w", pady=6
    )
    _label(2, "Format:")
    fmt_menu = tk.OptionMenu(win, fmt_var, *formats)
    fmt_menu.configure(bg=BTN_COLOR, fg=TEXT_COLOR, activebackground=BTN_HOVER,
                       activeforeground=TEXT_COLOR, relief="flat", highlightthickness=0,
                       font=("Segoe UI", 9))
    fmt_menu.grid(row=2, column=1, sticky="w", pady=6)

    def _ok() -> None:
        name = name_var.get().strip().upper()
        disk_id = id_var.get().strip().upper()
        if not name or len(name) > 16 or "," in name:
            messagebox.showwarning(
                "Ungültiger Name",
                "Der Disk-Name muss 1–16 Zeichen lang sein und darf kein Komma enthalten.",
                parent=win,
            )
            return
        if not disk_id or len(disk_id) > 2 or "," in disk_id:
            messagebox.showwarning(
                "Ungültige ID",
                "Die Disk-ID muss 1–2 Zeichen lang sein und darf kein Komma enthalten.",
                parent=win,
            )
            return
        result.append((name, disk_id, fmt_var.get()))
        win.destroy()

    btn_frame = tk.Frame(win, bg=BG_COLOR)
    btn_frame.grid(row=3, column=0, columnspan=2, pady=(6, 12))
    for text, cmd in (("Weiter …", _ok), ("Abbrechen", win.destroy)):
        tk.Button(
            btn_frame, text=text, command=cmd, bg=BTN_COLOR, fg=TEXT_COLOR,
            activebackground=BTN_HOVER, activeforeground=TEXT_COLOR,
            font=("Segoe UI", 9), relief="flat", cursor="hand2", padx=10, pady=4,
        ).pack(side="left", padx=6)

    win.bind("<Return>", lambda _e: _ok())
    win.bind("<Escape>", lambda _e: win.destroy())
    _center_on_parent(win, parent)
    win.transient(parent)
    win.grab_set()
    win.focus_set()
    parent.wait_window(win)
    return result[0] if result else None


# --------------------------------------------------------------------
# Bild-Hilfsfunktionen
# --------------------------------------------------------------------

def _open_and_prepare(icon_path: Path, size: tuple[int, int]) -> ImageTk.PhotoImage | None:
    """Oeffnet eine Bilddatei, skaliert auf die gewuenschte Groesse und bereitet sie fuer Tk vor."""
    try:
        img = Image.open(icon_path)
        if img.mode not in ("RGBA", "LA"):
            img = img.convert("RGBA")
        img.thumbnail(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except (OSError, ValueError) as e:
        _warn(f"Warnung: Bild '{icon_path.name}' konnte nicht geladen werden: {e}\n")
        return None


def load_icon(filename: str) -> ImageTk.PhotoImage | None:
    """Laedt ein Button-Icon. Faellt auf PLACEHOLDER_ICON zurueck, wenn das spezifische Icon fehlt."""
    if filename:
        icon_path = ICON_DIR / filename
        if icon_path.is_file():
            result = _open_and_prepare(icon_path, ICON_SIZE)
            if result is not None:
                return result

    if PLACEHOLDER_ICON:
        placeholder_path = ICON_DIR / PLACEHOLDER_ICON
        if placeholder_path.is_file():
            return _open_and_prepare(placeholder_path, ICON_SIZE)

    return None


def load_logo() -> ImageTk.PhotoImage | None:
    """Laedt das Logo von LOGO_PATH; faellt auf PLACEHOLDER_ICON zurueck wenn nicht gefunden."""
    if LOGO_PATH is not None and LOGO_PATH.is_file():
        return _open_and_prepare(LOGO_PATH, LOGO_SIZE)
    if PLACEHOLDER_ICON:
        placeholder_path = ICON_DIR / PLACEHOLDER_ICON
        if placeholder_path.is_file():
            return _open_and_prepare(placeholder_path, LOGO_SIZE)
    return None


def on_enter(event: tk.Event) -> None:
    event.widget.configure(bg=BTN_HOVER)


def on_leave(event: tk.Event) -> None:
    event.widget.configure(bg=BTN_COLOR)


# --------------------------------------------------------------------
# Katalog der Image-Formate
# --------------------------------------------------------------------

IMAGE_FORMAT_INFO = {
    "d64": "1541-Diskette, 170 KB (häufigstes Format)",
    "d67": "2040/3040-Diskette, 170 KB",
    "d71": "1571-Diskette, doppelseitig, 340 KB",
    "d80": "8050-Diskette, 500 KB",
    "d81": "1581-Diskette, 800 KB",
    "d82": "8250-Diskette, doppelseitig, 1 MB",
    "d90": "D9090-Festplatte",
    "g64": "1541-Rohabbild (GCR), auch mit Kopierschutz",
    "g71": "1571-Rohabbild (GCR)",
    "x64": "VICE-Diskettenabbild mit Kopfdaten (alt)",
    "t64": "Programmsammlung im Tape-Container",
    "tap": "Kassettenabbild (Originalsignal)",
    "prg": "Einzelnes Programm",
    "p00": "Einzelnes Programm im PC64-Container",
    "crt": "Steckmodul (Cartridge)",
}


def build_format_catalog() -> str:
    """Baut den Katalogtext: erst alle Endungen, dann je Emulator die passenden Endungen."""
    lines = ["Image-Endungen", ""]
    lines += [f".{ext}  –  {text}" for ext, text in IMAGE_FORMAT_INFO.items()]
    lines += ["", "─────────────────────────────────────────────", "", "Welcher Emulator liest was?", ""]
    for emu in EMULATORS:
        lines.append(f"{emu['label']}")
        lines.append("  Öffnen:  " + ", ".join(f".{e}" for e in emu["open"]))
        lines.append("  Neu anlegbar:  " + ", ".join(f".{e}" for e in emu["new"]))
        lines.append("")
    lines.append("Hinweis: Die Endung allein sagt nichts über den Rechner. Eine .d64 kann")
    lines.append("für C64, VIC-20, Plus/4 oder PET sein – der Launcher prüft deshalb beim")
    lines.append("Start die Startadresse des ersten Programms.")
    return "\n".join(lines)


def _show_text_popup(parent: tk.Tk, title: str, content: str, extra_button=None) -> None:
    """Zeigt einen modalen Textdialog mit scrollbarem Inhalt.
    extra_button = optional (Beschriftung, Funktion(popup_fenster)) fuer einen zusaetzlichen Button."""
    win = tk.Toplevel(parent)
    win.title(title)
    win.configure(bg=BG_COLOR)
    win.resizable(False, False)

    text_frame = tk.Frame(win, bg=BG_COLOR)
    text_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))

    scrollbar = tk.Scrollbar(text_frame, bg=BG_COLOR, troughcolor=FOOTER_BG)
    scrollbar.pack(side="right", fill="y")

    txt = tk.Text(
        text_frame,
        wrap="word",
        width=55,
        height=20,
        bg=BG_COLOR,
        fg=TEXT_COLOR,
        font=("Segoe UI", 9),
        relief="flat",
        bd=0,
        padx=15,
        pady=10,
        state="normal",
        cursor="arrow",
        selectbackground=BG_COLOR,
        selectforeground=TEXT_COLOR,
        yscrollcommand=scrollbar.set,
    )
    txt.insert("1.0", content)
    txt.configure(state="disabled")
    txt.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=txt.yview)

    btn_frame = tk.Frame(win, bg=BG_COLOR)
    btn_frame.pack(pady=10)
    buttons = [("Schließen", win.destroy)]
    if extra_button is not None:
        buttons.insert(0, (extra_button[0], lambda: extra_button[1](win)))
    for text, command in buttons:
        tk.Button(
            btn_frame,
            text=text,
            command=command,
            bg=BTN_COLOR,
            fg=TEXT_COLOR,
            activebackground=BTN_HOVER,
            activeforeground=TEXT_COLOR,
            font=("Segoe UI", 9),
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
        ).pack(side="left", padx=6)

    _center_on_parent(win, parent)
    win.transient(parent)
    win.grab_set()
    win.focus_set()


# --------------------------------------------------------------------
# UI-Hilfsfunktionen
# --------------------------------------------------------------------

def _make_link_label(
    parent: tk.Widget,
    text: str,
    action,
    bg: str = BG_COLOR,
    fg: str = LINK_COLOR,
) -> tk.Label:
    """Erstellt ein klickbares Label das action() aufruft und beim Hover die Farbe wechselt."""
    lbl = tk.Label(parent, text=text, font=("Segoe UI", 8), bg=bg, fg=fg, cursor="hand2")
    lbl.bind("<Button-1>", lambda _e: action())
    lbl.bind("<Enter>", lambda _e: lbl.configure(fg=TEXT_COLOR))
    lbl.bind("<Leave>", lambda _e: lbl.configure(fg=fg))
    return lbl


# --------------------------------------------------------------------
# UI-Aufbau
# --------------------------------------------------------------------
def build_ui() -> None:
    root = tk.Tk()
    root.title("The Emulator Launcher. For VICE - the Versatile Commodore Emulator!")
    root.withdraw()  # Erst sichtbar machen, wenn der VICE-Pfad feststeht

    vice_bin = resolve_vice_bin(parent=root)
    if vice_bin is None:
        messagebox.showerror(
            "Kein VICE gefunden",
            "Ohne VICE-Installation kann der Launcher nicht arbeiten.\n\n"
            "Bitte installiere VICE und starte den Launcher erneut.",
            parent=root,
        )
        root.destroy()
        return

    root.deiconify()
    # Fenster-Icon setzen (ersetzt die Tk-Feder)
    try:
        icon_img = Image.open(FAVICON_PATH)
        if icon_img.mode not in ("RGBA", "LA"):
            icon_img = icon_img.convert("RGBA")
        icon_photo = ImageTk.PhotoImage(icon_img)
        root.iconphoto(True, icon_photo)
        root._icon_ref = icon_photo  # Referenz halten
    except (OSError, ValueError) as e:
        _warn(f"Warnung: Fenster-Icon konnte nicht gesetzt werden: {e}\n")
    root.configure(bg=BG_COLOR)
    root.resizable(False, False)

    # --- Menü ---
    def _set_image_dir() -> None:
        cfg = load_config()
        chosen = filedialog.askdirectory(
            title="Standard Disk Image Ordner auswählen",
            initialdir=cfg.get("disk_image_dir") or str(Path.home()),
            parent=root,
        )
        if chosen:
            save_config({**cfg, "disk_image_dir": chosen})
            messagebox.showinfo(
                "Ordner gespeichert",
                f"Disk Images werden künftig in diesem Ordner geöffnet:\n\n{chosen}",
                parent=root,
            )

    def _clear_image_dir() -> None:
        cfg = load_config()
        if "disk_image_dir" not in cfg:
            messagebox.showinfo(
                "Kein Ordner gesetzt",
                "Es ist kein Standard Disk Image Ordner gesetzt.",
                parent=root,
            )
            return
        cfg.pop("disk_image_dir")
        save_config(cfg)
        messagebox.showinfo(
            "Ordner zurückgesetzt",
            "Der Standard Disk Image Ordner wurde entfernt.\n"
            "Der Datei-Dialog öffnet künftig den Standard-Speicherort.",
            parent=root,
        )

    def _image_dir() -> str:
        return load_config().get("disk_image_dir") or str(Path.home())

    def _new_image_and_start(emu: dict) -> None:
        opts = _ask_new_image(root, emu["label"], emu["new"])
        if opts is None:
            return
        name, disk_id, fmt = opts
        path = filedialog.asksaveasfilename(
            title=f"Neues {fmt.upper()}-Image speichern",
            initialdir=_image_dir(),
            initialfile=f"{name.lower().replace(' ', '_')}.{fmt}",
            defaultextension=f".{fmt}",
            filetypes=[(f"{fmt.upper()}-Image", f"*.{fmt}")],
            parent=root,
        )
        if not path:
            return
        error = create_disk_image(vice_bin, Path(path), name, disk_id, fmt)
        if error is not None:
            messagebox.showerror("Image konnte nicht erstellt werden", error, parent=root)
            return
        # Leeres Image nur in Laufwerk 8 einhaengen (Autostart faende kein Programm)
        launch_enhanced(root, vice_bin, emu["exe"], emu.get("args", []), path, attach_only=True)

    def _open_image_with(emu: dict) -> None:
        patterns = " ".join(f"*.{ext}" for ext in emu["open"])
        path = filedialog.askopenfilename(
            title=f"Image für {emu['label']} auswählen",
            initialdir=_image_dir(),
            filetypes=[(f"{emu['label']}-Images", patterns), ("Alle Dateien", "*.*")],
            parent=root,
        )
        if not path:
            return
        disk_image_var.set(path)
        disk_display_var.set(Path(path).name)
        launch_enhanced(root, vice_bin, emu["exe"], emu.get("args", []), path)

    def _save_format_pdf(win: tk.Toplevel) -> None:
        path = filedialog.asksaveasfilename(
            title="Image-Formate als PDF speichern",
            initialdir=_image_dir(),
            initialfile="VICE-Launcher_Image-Formate.pdf",
            defaultextension=".pdf",
            filetypes=[("PDF-Dokument", "*.pdf")],
            parent=win,
        )
        if not path:
            return
        try:
            from image_guide_pdf import create_format_pdf
            create_format_pdf(Path(path), EMULATORS, IMAGE_FORMAT_INFO, PDF_HEADER_PATH)
        except ImportError:
            messagebox.showerror(
                "PDF-Modul fehlt",
                "Für den PDF-Export wird 'reportlab' benötigt:\n\npip install reportlab",
                parent=win,
            )
            return
        except OSError as e:
            messagebox.showerror("PDF konnte nicht gespeichert werden", str(e), parent=win)
            return
        os.startfile(path)  # im Standard-PDF-Programm oeffnen

    def _show_format_catalog() -> None:
        _show_text_popup(root, "Image-Formate", build_format_catalog(),
                         extra_button=("Als PDF speichern …", _save_format_pdf))

    def _show_vice_path() -> None:
        _show_text_popup(
            root,
            "VICE-Pfad",
            f"VICE-Ordner (bin):\n{vice_bin}\n\n"
            f"Konfigurationsdatei:\n{CONFIG_PATH}\n\n"
            f"Disk Image Ordner:\n{load_config().get('disk_image_dir') or '– nicht gesetzt –'}",
        )

    menubar = tk.Menu(root, bg="#1f1575", fg=TEXT_COLOR,
                      activebackground=BTN_HOVER, activeforeground=TEXT_COLOR,
                      relief="flat", bd=0)

    file_menu = tk.Menu(menubar, tearoff=0, bg="#1f1575", fg=TEXT_COLOR,
                        activebackground=BTN_HOVER, activeforeground=TEXT_COLOR)
    file_menu.add_command(label="Beenden", command=root.quit, accelerator="Alt+F4")
    menubar.add_cascade(label="Datei", menu=file_menu)

    image_menu = tk.Menu(menubar, tearoff=0, bg="#1f1575", fg=TEXT_COLOR,
                         activebackground=BTN_HOVER, activeforeground=TEXT_COLOR)
    new_menu = tk.Menu(image_menu, tearoff=0, bg="#1f1575", fg=TEXT_COLOR,
                       activebackground=BTN_HOVER, activeforeground=TEXT_COLOR)
    open_menu = tk.Menu(image_menu, tearoff=0, bg="#1f1575", fg=TEXT_COLOR,
                        activebackground=BTN_HOVER, activeforeground=TEXT_COLOR)
    for emu in EMULATORS:
        new_menu.add_command(label=emu["label"], command=lambda e=emu: _new_image_and_start(e))
        open_menu.add_command(label=emu["label"], command=lambda e=emu: _open_image_with(e))
    image_menu.add_cascade(label="Neues Image erstellen und starten mit", menu=new_menu)
    image_menu.add_cascade(label="Vorhandenes Image starten mit", menu=open_menu)
    menubar.add_cascade(label="Image", menu=image_menu)

    settings_menu = tk.Menu(menubar, tearoff=0, bg="#1f1575", fg=TEXT_COLOR,
                             activebackground=BTN_HOVER, activeforeground=TEXT_COLOR)
    settings_menu.add_command(label="Disk Image Ordner festlegen …", command=_set_image_dir)
    settings_menu.add_command(label="Disk Image Ordner zurücksetzen", command=_clear_image_dir)
    menubar.add_cascade(label="Einstellungen", menu=settings_menu)

    info_menu = tk.Menu(menubar, tearoff=0, bg="#1f1575", fg=TEXT_COLOR,
                        activebackground=BTN_HOVER, activeforeground=TEXT_COLOR)
    info_menu.add_command(label="Image-Formate …", command=_show_format_catalog)
    info_menu.add_command(label="VICE-Pfad …", command=_show_vice_path)
    info_menu.add_separator()
    info_menu.add_command(
        label="Lizenz: GNU GPL v3",
        command=lambda: webbrowser.open("https://www.gnu.org/licenses/gpl-3.0.html"),
    )
    menubar.add_cascade(label="Info", menu=info_menu)

    root.config(menu=menubar)

    # Spalten gleichmaessig verteilen (noetig fuer sticky="ew" in Footer/Disk-Frame)
    for c in range(COLUMNS):
        root.grid_columnconfigure(c, weight=1)

    # --- Header ---
    tk.Label(
        root,
        text="The Emulator Launcher. For VICE.",
        font=("Segoe UI", 16, "bold"),
        bg=BG_COLOR,
        fg=TEXT_COLOR,
    ).grid(row=0, column=0, columnspan=COLUMNS, pady=(20, 5), padx=20)

    # --- Logo ---
    logo = load_logo()
    if logo is not None:
        logo_label = tk.Label(root, image=logo, bg=BG_COLOR, bd=0)
        # Referenz festhalten, sonst killt der Garbage Collector das Bild
        logo_label.image = logo
        logo_label.grid(row=1, column=0, columnspan=COLUMNS, pady=(5, 15))
    else:
        tk.Label(
            root,
            text="by Retrokauz",
            font=("Segoe UI", 9),
            bg=BG_COLOR,
            fg=MUTED_COLOR,
        ).grid(row=1, column=0, columnspan=COLUMNS, pady=(0, 15))

    # --- Disk-Image-Zustand (muss vor den Buttons definiert sein) ---
    disk_image_var   = tk.StringVar(value="")
    disk_display_var = tk.StringVar(value="– kein Image –")

    # --- Emulator-Buttons ---
    last_emu_row = 2 + (len(EMULATORS) - 1) // COLUMNS

    for idx, emu in enumerate(EMULATORS):
        row = 2 + idx // COLUMNS
        col = idx % COLUMNS

        icon     = load_icon(emu.get("icon", ""))
        has_icon = icon is not None

        btn = tk.Button(
            root,
            text=emu["label"],
            image=icon if has_icon else "",
            compound="top" if has_icon else "center",
            width=BTN_WIDTH,
            height=BTN_HEIGHT_WITH_ICON if has_icon else BTN_HEIGHT_TEXT_ONLY,
            bg=BTN_COLOR,
            fg=TEXT_COLOR,
            activebackground=BTN_HOVER,
            activeforeground=TEXT_COLOR,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
            command=lambda e=emu["exe"], a=emu.get("args", []): launch_enhanced(
                root, vice_bin, e, a, disk_image_var.get()
            ),
        )
        if has_icon:
            btn.image = icon

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.grid(row=row, column=col, padx=10, pady=10)

    # --- Disk-Image-Auswahl ---
    disk_row = last_emu_row + 1

    disk_frame = tk.Frame(root, bg=DISK_BG)
    disk_frame.grid(row=disk_row, column=0, columnspan=COLUMNS, padx=0, pady=(6, 0), sticky="ew")

    tk.Label(
        disk_frame,
        text="Disk Image:",
        font=("Segoe UI", 9),
        bg=DISK_BG,
        fg=MUTED_COLOR,
    ).pack(side="left", padx=(12, 6), pady=6)

    tk.Entry(
        disk_frame,
        textvariable=disk_display_var,
        font=("Segoe UI", 9),
        bg="white",
        fg="#1a1060",
        readonlybackground="white",
        state="readonly",
        relief="flat",
        bd=2,
        width=30,
    ).pack(side="left", padx=(0, 6), pady=6, ipady=2)

    def _select_image() -> None:
        # Immer explizit initialdir setzen – der Windows-COM-Dialog merkt sich sonst
        # intern das zuletzt verwendete Verzeichnis, unabhängig von unserer config.json.
        initial_dir = load_config().get("disk_image_dir") or str(Path.home())
        path = filedialog.askopenfilename(
            title="Disk Image auswählen",
            initialdir=initial_dir,
            filetypes=[
                (
                    "VICE Images",
                    "*.d64 *.d71 *.d80 *.d81 *.d82 *.g64 *.g71 *.x64 *.t64 *.prg *.p00",
                ),
                ("Alle Dateien", "*.*"),
            ],
            parent=root,
        )
        if path:
            disk_image_var.set(path)
            disk_display_var.set(Path(path).name)

    def _clear_image() -> None:
        disk_image_var.set("")
        disk_display_var.set("– kein Image –")

    tk.Button(
        disk_frame,
        text="Laden …",
        command=_select_image,
        font=("Segoe UI", 9),
        bg="#4a38c0",
        fg=TEXT_COLOR,
        activebackground="#6655d8",
        activeforeground=TEXT_COLOR,
        relief="flat",
        cursor="hand2",
        padx=8,
        pady=2,
    ).pack(side="left", padx=(0, 4))

    tk.Button(
        disk_frame,
        text="×",
        command=_clear_image,
        font=("Segoe UI", 9),
        bg="#8b2828",
        fg=TEXT_COLOR,
        activebackground="#aa3333",
        activeforeground=TEXT_COLOR,
        relief="flat",
        cursor="hand2",
        padx=6,
        pady=2,
    ).pack(side="left")

    # --- Trennlinie ---
    sep_row = disk_row + 1
    tk.Frame(root, bg="#3d2fbf", height=1).grid(
        row=sep_row, column=0, columnspan=COLUMNS, sticky="ew"
    )

    # --- Footer ---
    footer_row = sep_row + 1
    footer_frame = tk.Frame(root, bg=FOOTER_BG)
    footer_frame.grid(row=footer_row, column=0, columnspan=COLUMNS, sticky="ew")

    _make_link_label(
        footer_frame,
        "info@retrokauz.de",
        lambda: webbrowser.open("mailto:info@retrokauz.de"),
        bg=FOOTER_BG,
    ).pack(side="left", padx=(12, 0), pady=6)

    tk.Label(
        footer_frame, text="|", font=("Segoe UI", 8), bg=FOOTER_BG, fg=MUTED_COLOR
    ).pack(side="left", padx=6, pady=6)

    _make_link_label(
        footer_frame,
        "www.retrokauz.de",
        lambda: webbrowser.open("https://www.retrokauz.de"),
        bg=FOOTER_BG,
    ).pack(side="left", pady=6)


    # --- Fenster positionieren - auf Primaermonitor, mittig ---
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = max(0, (screen_w - w) // 2)
    y = max(0, (screen_h - h) // 2)
    root.geometry(f"+{x}+{y}")

    # Kurz in den Vordergrund holen, damit man den Launcher bei
    # Multi-Monitor-Setups sicher findet.
    root.lift()
    root.attributes("-topmost", True)
    root.after(500, lambda: root.attributes("-topmost", False))

    root.mainloop()


if __name__ == "__main__":
    build_ui()
