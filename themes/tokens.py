"""
VICE Launcher — Design tokens (Python / PySide6)

Importable token module so the Python code doesn't have to hard-code hex
values. Two themes are provided. Load the matching .qss file to style
widgets, but use these tokens for anything you paint manually
(QPainter, QPixmap, dynamic QSS snippets, etc.).

Usage:
    from themes.tokens import THEMES, EMULATORS
    t = THEMES["pixel"]
    label.setStyleSheet(f"color: {t['accent']};")
"""

THEMES = {
    "pixel": {
        "name":         "Pixel Workshop",
        "bg":           "#0E0A2E",
        "bg_raised":    "#15103D",
        "card":         "#06030F",
        "card_border":  "#2A1F6B",
        "accent":       "#4F3FD6",
        "accent_soft":  "#27188E",
        "accent_glow":  "rgba(123, 104, 238, 0.35)",
        "text":         "#F2F0FF",
        "text_muted":   "#9A95C8",
        "text_dim":     "#5B568A",
        "success":      "#4ADE80",
        "warn":         "#F5C451",
        "danger":       "#F26464",
        "font_ui":      'Geist, Inter, "Segoe UI", sans-serif',
        "font_mono":    '"JetBrains Mono", Consolas, monospace',
        "radius":       6,
        "radius_lg":    10,
        "qss_file":     "pixel.qss",
    },
    "c64": {
        "name":         "C64 Homage",
        "bg":           "#40318D",
        "bg_raised":    "#4B3BA3",
        "card":         "#352784",
        "card_border":  "#7B68EE",
        "accent":       "#A59CFF",
        "accent_soft":  "#6C5CE7",
        "accent_glow":  "rgba(165, 156, 255, 0.4)",
        "text":         "#EEEAFF",
        "text_muted":   "#B5AEEA",
        "text_dim":     "#7B6FBF",
        "success":      "#B8F27D",
        "warn":         "#FFE15D",
        "danger":       "#FF7A7A",
        "font_ui":      'Inter, "Segoe UI", sans-serif',
        "font_mono":    '"JetBrains Mono", Consolas, monospace',
        "radius":       4,
        "radius_lg":    8,
        "qss_file":     "c64.qss",
    },
}

# Full VICE emulator catalog. `color` is the accent used in the machine icon.
EMULATORS = [
    {"id": "x64sc",   "label": "C64",         "sub": "Commodore 64 (accurate)", "exe": "x64sc",   "color": "#7B68EE"},
    {"id": "x64dtv",  "label": "C64 DTV",     "sub": "DTV console",             "exe": "x64dtv",  "color": "#F5C451"},
    {"id": "xscpu64", "label": "SuperCPU 64", "sub": "C64 + SuperCPU",          "exe": "xscpu64", "color": "#4ADE80"},
    {"id": "x128",    "label": "C128",        "sub": "Commodore 128",           "exe": "x128",    "color": "#6EE7F9"},
    {"id": "xvic",    "label": "VIC-20",      "sub": "VIC-20",                  "exe": "xvic",    "color": "#F78DA7"},
    {"id": "xplus4",  "label": "Plus/4",      "sub": "Plus/4 & C16",            "exe": "xplus4",  "color": "#B8F27D"},
    {"id": "xpet",    "label": "PET",         "sub": "PET series",              "exe": "xpet",    "color": "#C9B5FF"},
    {"id": "xcbm2",   "label": "CBM-II",      "sub": "600/700 series",          "exe": "xcbm2",   "color": "#FFB86B"},
    {"id": "xcbm5x0", "label": "CBM 5x0",     "sub": "500 series",              "exe": "xcbm5x0", "color": "#FF7A7A"},
]

TOOLS = [
    {"id": "c1541",    "label": "c1541",    "sub": "Disk image tool"},
    {"id": "petcat",   "label": "petcat",   "sub": "BASIC lister"},
    {"id": "cartconv", "label": "cartconv", "sub": "Cart converter"},
]

# Platform executable suffix — append this when building paths.
# On Windows VICE binaries end in .exe; on mac/linux they don't.
import sys
EXE_SUFFIX = ".exe" if sys.platform.startswith("win") else ""
