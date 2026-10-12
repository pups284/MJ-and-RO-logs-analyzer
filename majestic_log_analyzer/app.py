from __future__ import annotations
import sys

from PySide6.QtWidgets import QApplication

from .style import STYLE
from .ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Majestic Log Analyzer")
    app.setStyleSheet(STYLE)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())