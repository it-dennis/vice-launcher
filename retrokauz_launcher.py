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

# Vollstaendiger Pfad zum Favicon.
FAVICON_PATH = APP_DIR / "favicon" / "favicon.ico"

# Wird automatisch geladen, wenn das spezifische Icon eines Emulators fehlt.
# Auf None setzen, falls kein Fallback gewuenscht ist.
PLACEHOLDER_ICON = "placeholder_logo.png"

# Unterstuetzte Formate: PNG, JPG, JPEG, GIF, BMP, ICO, WEBP, TIFF
# args = optionale Kommandozeilen-Argumente pro Emulator, z.B. ["-fullscreen"]
EMULATORS = [
    {"label": "X64sc",        "exe": "x64sc.exe",   "icon": "vicelauncher_button.png", "args": []},
    {"label": "C128",         "exe": "x128.exe",    "icon": "vicelauncher_button.png", "args": []},
    {"label": "VIC-20",       "exe": "xvic.exe",    "icon": "vicelauncher_button.png", "args": []},
    {"label": "Plus/4 & C16", "exe": "xplus4.exe",  "icon": "vicelauncher_button.png", "args": []},
    {"label": "PET",          "exe": "xpet.exe",    "icon": "vicelauncher_button.png", "args": []},
    {"label": "C64 DTV",      "exe": "x64dtv.exe",  "icon": "vicelauncher_button.png", "args": []},
    {"label": "SuperCPU64",   "exe": "xscpu64.exe", "icon": "vicelauncher_button.png", "args": []},
    {"label": "CBM-II",       "exe": "xcbm2.exe",   "icon": "vicelauncher_button.png", "args": []},
    {"label": "CBM-5x0",      "exe": "xcbm5x0.exe", "icon": "vicelauncher_button.png", "args": []},
]

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

def _find_window_for_pid(pid: int) -> int | None:
    """Gibt das HWND des ersten sichtbaren Hauptfensters eines Prozesses zurueck."""
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
    return found[0] if found else None


def _position_beside_launcher(root: tk.Tk, hwnd: int) -> None:
    """Verschiebt das Emulator-Fenster rechts neben den Launcher."""
    root.update_idletasks()
    x = root.winfo_x() + root.winfo_width() + 10
    y = root.winfo_y()
    SWP_NOSIZE   = 0x0001
    SWP_NOZORDER = 0x0004
    ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, 0, 0, SWP_NOSIZE | SWP_NOZORDER)


class _MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize",    ctypes.c_ulong),
        ("rcMonitor", ctypes.wintypes.RECT),
        ("rcWork",    ctypes.wintypes.RECT),
        ("dwFlags",   ctypes.c_ulong),
    ]


def _is_window_fullscreen(hwnd: int) -> bool:
    """Prueft ob ein Fenster den gesamten Monitor belegt (Vollbild oder maximiert)."""
    win_rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(win_rect))

    MONITOR_DEFAULTTONEAREST = 2
    hmon = ctypes.windll.user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)

    mi = _MONITORINFO()
    mi.cbSize = ctypes.sizeof(_MONITORINFO)
    ctypes.windll.user32.GetMonitorInfoW(hmon, ctypes.byref(mi))

    m = mi.rcMonitor
    return (
        win_rect.left <= m.left
        and win_rect.top <= m.top
        and win_rect.right >= m.right
        and win_rect.bottom >= m.bottom
    )


def _monitor_vice_window(root: tk.Tk, hwnd: int, was_fullscreen: bool) -> None:
    """Pollt das VICE-Fenster und positioniert es nach dem Verlassen des Vollbilds neu."""
    if not ctypes.windll.user32.IsWindow(hwnd):
        return  # VICE wurde geschlossen – Monitoring beenden

    is_fs = _is_window_fullscreen(hwnd)

    if was_fullscreen and not is_fs:
        # Kurze Pause, damit VICE die Fenster-Animation abschliessen kann
        root.after(200, lambda: _position_beside_launcher(root, hwnd))

    root.after(500, lambda: _monitor_vice_window(root, hwnd, is_fs))


def _poll_for_window(root: tk.Tk, pid: int, remaining: int, delay_ms: int = 250) -> None:
    """Pollt auf das Prozessfenster und positioniert es, sobald es erscheint."""
    hwnd = _find_window_for_pid(pid)
    if hwnd:
        _position_beside_launcher(root, hwnd)
        # Monitoring starten: repositioniert VICE automatisch nach Vollbild-Exit
        root.after(500, lambda: _monitor_vice_window(root, hwnd, False))
        return
    if remaining > 1:
        root.after(delay_ms, lambda: _poll_for_window(root, pid, remaining - 1, delay_ms))


def launch_enhanced(
    root: tk.Tk,
    vice_bin: Path,
    exe_name: str,
    args: list[str],
    disk_image: str,
) -> None:
    """Startet den Emulator, laedt optional ein Disk-Image und positioniert das Fenster."""
    exe_path = vice_bin / exe_name
    if not exe_path.is_file():
        messagebox.showerror(
            "Datei nicht gefunden",
            f"Die Datei existiert nicht:\n\n{exe_path}\n\n"
            f"Bitte den VICE-Ordner pruefen "
            f"(Konfigurationsdatei: {CONFIG_PATH}).",
        )
        return

    cmd = [str(exe_path), *args]
    if disk_image:
        cmd += ["-autostart", disk_image]

    try:
        proc = subprocess.Popen(cmd, cwd=str(vice_bin))
        # Max. 5 Sekunden auf das VICE-Fenster warten (20 x 250 ms)
        _poll_for_window(root, proc.pid, remaining=20, delay_ms=250)
    except OSError as e:
        messagebox.showerror("Startfehler", f"{exe_name} konnte nicht gestartet werden:\n\n{e}")


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
# Impressum & Datenschutz
# --------------------------------------------------------------------

IMPRESSUM_TEXT = """\
Impressum

Angaben gemäß § 5 TMG

[Vorname Nachname / Firmenname]
[Straße und Hausnummer]
[PLZ Ort]
Deutschland

Kontakt:
E-Mail:  info@retrokauz.de
Web:     www.retrokauz.de

─────────────────────────────────────────────────────

Retrokauz ist ein privates Hobby-Projekt.
Retrokauz – The VICE Launcher ist kostenlose Software (Freeware).

VICE (Versatile Commodore Emulator) wird vom VICE-Team entwickelt
und steht unter der GNU General Public License v2+.
Weitere Informationen: https://vice-emu.sourceforge.io/

Für den Inhalt verlinkter externer Webseiten übernehmen wir
keine Haftung.
"""

DATENSCHUTZ_TEXT = """\
Datenschutzerklärung

1. Verantwortlicher
[Vorname Nachname]
E-Mail: info@retrokauz.de
Web:    www.retrokauz.de

─────────────────────────────────────────────────────

2. Welche Daten werden gespeichert?
Retrokauz – The VICE Launcher speichert ausschließlich den Pfad
zum VICE-Installationsordner lokal auf deinem Computer:

  %APPDATA%\\retrokauz\\vice-launcher\\config.json

Es werden keine personenbezogenen Daten erhoben.
Es werden keine Daten an Server übertragen.
Es gibt keine Cookies, kein Tracking, keine Analyse.

3. Keine Weitergabe an Dritte
Alle gespeicherten Daten verbleiben ausschließlich auf deinem
Gerät. Eine Weitergabe an Dritte findet nicht statt.

4. Deine Rechte
Du kannst deine gespeicherte Konfiguration jederzeit löschen:
  %APPDATA%\\retrokauz\\vice-launcher\\

Für Datenschutzanfragen: info@retrokauz.de

5. Hinweis zu VICE
VICE ist ein eigenständiges Programm des VICE-Teams (GNU GPL v2+).
Für dessen Datenschutzpraktiken sind wir nicht verantwortlich.
"""


def _show_text_popup(parent: tk.Tk, title: str, content: str) -> None:
    """Zeigt einen modalen Textdialog mit scrollbarem Inhalt."""
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

    tk.Button(
        win,
        text="Schließen",
        command=win.destroy,
        bg=BTN_COLOR,
        fg=TEXT_COLOR,
        activebackground=BTN_HOVER,
        activeforeground=TEXT_COLOR,
        font=("Segoe UI", 9),
        relief="flat",
        cursor="hand2",
        padx=10,
        pady=4,
    ).pack(pady=10)

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

    menubar = tk.Menu(root, bg="#1f1575", fg=TEXT_COLOR,
                      activebackground=BTN_HOVER, activeforeground=TEXT_COLOR,
                      relief="flat", bd=0)

    file_menu = tk.Menu(menubar, tearoff=0, bg="#1f1575", fg=TEXT_COLOR,
                        activebackground=BTN_HOVER, activeforeground=TEXT_COLOR)
    file_menu.add_command(label="Beenden", command=root.quit, accelerator="Alt+F4")
    menubar.add_cascade(label="Datei", menu=file_menu)

    settings_menu = tk.Menu(menubar, tearoff=0, bg="#1f1575", fg=TEXT_COLOR,
                             activebackground=BTN_HOVER, activeforeground=TEXT_COLOR)
    settings_menu.add_command(label="Disk Image Ordner festlegen …", command=_set_image_dir)
    settings_menu.add_command(label="Disk Image Ordner zurücksetzen", command=_clear_image_dir)
    menubar.add_cascade(label="Einstellungen", menu=settings_menu)

    info_menu = tk.Menu(menubar, tearoff=0, bg="#1f1575", fg=TEXT_COLOR,
                        activebackground=BTN_HOVER, activeforeground=TEXT_COLOR)
    info_menu.add_command(
        label="Impressum",
        command=lambda: _show_text_popup(root, "Impressum", IMPRESSUM_TEXT),
    )
    info_menu.add_command(
        label="Datenschutzerklärung",
        command=lambda: _show_text_popup(root, "Datenschutzerklärung", DATENSCHUTZ_TEXT),
    )
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
