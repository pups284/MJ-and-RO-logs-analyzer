from __future__ import annotations
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .storage import APP_DIR
from .style import STYLE
from .ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Majestic Log Analyzer")
    app.setStyleSheet(STYLE)

    icon_path = APP_DIR / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    win = MainWindow()
    win.showMaximized()
    sys.exit(app.exec())