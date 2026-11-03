from __future__ import annotations

import sys
import ctypes
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication

from . import bridge
from .storage import APP_DIR
from .style import STYLE, apply_app_font
from .ui.main_window import MainWindow


SERVER_NAME = bridge.SERVER_NAME


def _send_to_existing(paths: list[str]) -> bool:
    socket = QLocalSocket()
    socket.connectToServer(SERVER_NAME)
    if not socket.waitForConnected(300):
        return False

    if sys.platform == "win32":
        try:
            ctypes.windll.user32.AllowSetForegroundWindow(-1)
        except Exception:
            pass

    payload = bridge.encode_open_paths(paths, auto_open=False) + b"\n"
    socket.write(payload)
    socket.flush()
    socket.waitForBytesWritten(500)
    socket.disconnectFromServer()
    return True


def _force_foreground(hwnd: int):
    if sys.platform != "win32":
        return
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)

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
    app.setStyle("Fusion")
    apply_app_font(app)
    app.setStyleSheet(STYLE)

    base_path = Path(getattr(sys, "_MEIPASS", APP_DIR))
    for icon_name in ("icon.ico", "icon.png"):
        icon_path = base_path / icon_name
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
            break

    cli_paths = [p for p in sys.argv[1:] if p and Path(p).is_file()]

    if _send_to_existing(cli_paths):
        sys.exit(0)

    QLocalServer.removeServer(SERVER_NAME)
    server = QLocalServer()
    server.listen(SERVER_NAME)

    win = MainWindow()
    win.showMaximized()

    def _bring_to_front():
        if win.isMinimized():
            win.showNormal()
        if not win.isActiveWindow():
            win.raise_()
            win.activateWindow()
            _force_foreground(int(win.winId()))

    def _process_request(raw: bytes):
        try:
            request = bridge.parse_request(raw)
            paths = list(request.paths)
            paths.extend(bridge.materialize(request.inline_files))
        except Exception as exc:
            print(f"[bridge] rejected request: {exc}")
            return

        if paths:
            win.analyze_tab.add_files(paths, auto_open=request.auto_open)
        _bring_to_front()

    def _handle_socket(sock: QLocalSocket):
        state = {"buffer": bytearray(), "done": False}

        def finish():
            if state["done"]:
                return
            state["done"] = True
            _process_request(bytes(state["buffer"]))
            sock.deleteLater()

        def read():
            if state["done"]:
                return
            chunk = sock.readAll().data()
            if not chunk:
                return

            state["buffer"].extend(chunk)
            if len(state["buffer"]) > bridge.MAX_REQUEST_BYTES:
                state["done"] = True
                sock.abort()
                sock.deleteLater()
                return

            if b"\n" in chunk:
                finish()
                sock.disconnectFromServer()

        sock.readyRead.connect(read)
        sock.disconnected.connect(finish)

    def _on_new_connection():
        sock = server.nextPendingConnection()
        _handle_socket(sock)

    server.newConnection.connect(_on_new_connection)

    if cli_paths:
        QTimer.singleShot(100, lambda: win.analyze_tab.add_files(cli_paths))

    sys.exit(app.exec())