"""
VICE Launcher — Minimal PySide6 bootstrap showing how to wire the themes.

This is a *starting point*, not the full app. It demonstrates:
  • Loading pixel.qss or c64.qss at runtime
  • Live theme switching via QApplication.setStyleSheet
  • Persisting the chosen theme to ~/.config/retrokauz/vice-launcher.json
  • Using the object names the QSS targets (#Sidebar, #EmulatorCard, ...)

Run:
    pip install PySide6
    python launcher_skeleton.py
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QFrame, QGridLayout, QLineEdit,
)

from tokens import THEMES, EMULATORS  # themes/tokens.py

# ------------------------------------------------------------
# Settings persistence
# ------------------------------------------------------------
def settings_path() -> Path:
    if sys.platform.startswith("win"):
        base = Path.home() / "AppData" / "Roaming"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    d = base / "retrokauz" / "vice-launcher"
    d.mkdir(parents=True, exist_ok=True)
    return d / "settings.json"


def load_settings() -> dict:
    p = settings_path()
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"theme": "pixel", "vice_path": None}


def save_settings(data: dict) -> None:
    settings_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


# ------------------------------------------------------------
# Theme loader
# ------------------------------------------------------------
def apply_theme(app: QApplication, theme_key: str) -> None:
    qss_file = Path(__file__).parent / THEMES[theme_key]["qss_file"]
    app.setStyleSheet(qss_file.read_text(encoding="utf-8"))


# ------------------------------------------------------------
# Main window
# ------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, app: QApplication, settings: dict):
        super().__init__()
        self.app = app
        self.settings = settings
        self.setWindowTitle("VICE Launcher")
        self.resize(1040, 680)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_sidebar())
        layout.addWidget(self._build_main(), 1)

    def _build_sidebar(self) -> QWidget:
        side = QFrame()
        side.setObjectName("Sidebar")
        v = QVBoxLayout(side)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        brand = QLabel("VICE Launcher")
        brand.setObjectName("SidebarBrand")
        version = QLabel("by retrokauz · v1.0")
        version.setObjectName("SidebarVersion")
        v.addWidget(brand)
        v.addWidget(version)

        for label, active in [
            ("▤  All Machines", True),
            ("✦  Favorites", False),
            ("↻  Recently played", False),
            ("◉  Games", False),
            ("⚙  Tools", False),
        ]:
            btn = QPushButton(label)
            btn.setObjectName("SidebarItemActive" if active else "SidebarItem")
            btn.setCursor(Qt.PointingHandCursor)
            v.addWidget(btn)

        v.addStretch(1)

        # Theme toggle — the real user-facing feature
        toggle_row = QHBoxLayout()
        for key in ("pixel", "c64"):
            b = QPushButton("A·Pixel" if key == "pixel" else "B·C64")
            b.setObjectName("PrimaryButton" if key == self.settings["theme"] else "SecondaryButton")
            b.clicked.connect(lambda _=False, k=key: self._switch_theme(k))
            toggle_row.addWidget(b)
        wrapper = QWidget()
        wrapper.setLayout(toggle_row)
        v.addWidget(wrapper)

        status = QLabel("● VICE 3.8 · detected")
        status.setObjectName("StatusPill")
        v.addWidget(status)

        return side

    def _build_main(self) -> QWidget:
        main = QWidget()
        v = QVBoxLayout(main)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # Toolbar
        tb = QFrame()
        tb.setObjectName("Toolbar")
        h = QHBoxLayout(tb)
        title = QLabel("All Machines")
        title.setObjectName("ToolbarTitle")
        sub = QLabel("9 emulators")
        sub.setObjectName("ToolbarSub")
        h.addWidget(title)
        h.addWidget(sub)
        h.addStretch(1)
        search_wrap = QFrame()
        search_wrap.setObjectName("SearchBox")
        sw = QHBoxLayout(search_wrap)
        sw.setContentsMargins(8, 2, 8, 2)
        search = QLineEdit()
        search.setObjectName("SearchInput")
        search.setPlaceholderText("Search games, disks, tools…")
        sw.addWidget(search)
        h.addWidget(search_wrap)
        v.addWidget(tb)

        # Drop hint
        hint = QLabel("↓  Drag a .d64, .tap, .prg or .crt anywhere to auto-launch")
        hint.setObjectName("DropHint")
        v.addWidget(hint)

        # Emulator grid
        grid_wrap = QWidget()
        grid = QGridLayout(grid_wrap)
        grid.setContentsMargins(20, 14, 20, 20)
        grid.setSpacing(14)
        for idx, emu in enumerate(EMULATORS):
            grid.addWidget(self._emulator_card(emu), idx // 3, idx % 3)
        v.addWidget(grid_wrap, 1)

        return main

    def _emulator_card(self, emu: dict) -> QWidget:
        card = QFrame()
        card.setObjectName("EmulatorCard")
        v = QVBoxLayout(card)

        title = QLabel(emu["label"])
        title.setObjectName("EmulatorTitle")
        sub = QLabel(emu["sub"])
        sub.setObjectName("EmulatorSub")
        exe = QLabel(emu["exe"])
        exe.setObjectName("EmulatorExe")
        v.addWidget(title)
        v.addWidget(sub)
        v.addWidget(exe)

        launch = QPushButton("▶ Launch")
        launch.setObjectName("PrimaryButton")
        launch.clicked.connect(lambda _=False, e=emu: self._launch(e))
        v.addWidget(launch)
        return card

    def _launch(self, emu: dict) -> None:
        # TODO: use VICE-detection module to resolve bin path, then QProcess.startDetached
        print(f"[TODO] launch {emu['exe']} (path resolution goes here)")

    def _switch_theme(self, key: str) -> None:
        self.settings["theme"] = key
        save_settings(self.settings)
        apply_theme(self.app, key)
        # Rebuild to pick up active-button style; full app should diff instead.
        self.centralWidget().deleteLater()
        new_root = QWidget()
        self.setCentralWidget(new_root)
        layout = QHBoxLayout(new_root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar())
        layout.addWidget(self._build_main(), 1)


def main() -> int:
    app = QApplication(sys.argv)
    settings = load_settings()
    apply_theme(app, settings["theme"])
    win = MainWindow(app, settings)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
