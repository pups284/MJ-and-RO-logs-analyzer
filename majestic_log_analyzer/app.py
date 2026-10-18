from __future__ import annotations

import sys
import ctypes
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication

from .storage import APP_DIR
from .style import STYLE
from .ui.main_window import MainWindow


SERVER_NAME = "MajesticLogAnalyzer_SingleInstance"


def _send_to_existing(paths: list[str]) -> bool:
    """Отправляет пути уже запущенному экземпляру. Возвращает True, если он есть."""
    socket = QLocalSocket()
    socket.connectToServer(SERVER_NAME)
    if not socket.waitForConnected(300):
        return False

    if sys.platform == "win32":
        try:
            ctypes.windll.user32.AllowSetForegroundWindow(-1)
        except Exception:
            pass

    payload = b"\0".join(p.encode("utf-8") for p in paths if p)
    socket.write(payload)
    socket.flush()
    socket.waitForBytesWritten(500)
    socket.disconnectFromServer()
    return True


def _force_foreground(hwnd: int):
    """Жёсткий вывод окна на передний план в Windows (без минимизации)."""
    if sys.platform != "win32":
        return
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        # Восстанавливаем, если свернуто
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE

        foreground_hwnd = user32.GetForegroundWindow()
        foreground_tid = user32.GetWindowThreadProcessId(foreground_hwnd, None)
        current_tid = kernel32.GetCurrentThreadId()

        if foreground_tid != current_tid:
            user32.AttachThreadInput(foreground_tid, current_tid, True)

        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)

        if foreground_tid != current_tid:
            user32.AttachThreadInput(foreground_tid, current_tid, False)
    except Exception as e:
        print(f"force_foreground failed: {e}")


def main() -> None:
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("majestic.log.analyzer")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("Majestic Log Analyzer")
    app.setStyleSheet(STYLE)

    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = APP_DIR

    icon_ico = base_path / "icon.ico"
    icon_png = base_path / "icon.png"
    
    if icon_ico.exists():
        app.setWindowIcon(QIcon(str(icon_ico)))
    elif icon_png.exists():
        app.setWindowIcon(QIcon(str(icon_png)))

    cli_paths = [p for p in sys.argv[1:] if p and Path(p).is_file()]

    if _send_to_existing(cli_paths):
        sys.exit(0)

    QLocalServer.removeServer(SERVER_NAME)
    server = QLocalServer()
    server.listen(SERVER_NAME)

    win = MainWindow()
    win.showMaximized()

    def _on_new_connection():
        sock = server.nextPendingConnection()
        sock.readyRead.connect(lambda s=sock: _handle_socket(s))

    def _handle_socket(sock: QLocalSocket):
        data = sock.readAll().data().decode("utf-8", errors="replace")
        sock.disconnectFromServer()
        paths = [p for p in data.split("\0") if p]
        
        if paths:
            win.analyze_tab.add_files(paths)
            
            # Если окно свернуто в панель задач — разворачиваем
            if win.isMinimized():
                win.showNormal()
            
            # Выводим на передний план ТОЛЬКО если оно сейчас не активно
            if not win.isActiveWindow():
                win.raise_()
                win.activateWindow()
                _force_foreground(int(win.winId()))

    server.newConnection.connect(_on_new_connection)

    if cli_paths:
        QTimer.singleShot(100, lambda: win.analyze_tab.add_files(cli_paths))

    sys.exit(app.exec())