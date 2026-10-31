from __future__ import annotations
import sys


def apply_dark_title_bar(widget) -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        is_light = bool(app and app.property("theme") == "light")
        hwnd = int(widget.winId())
        value = ctypes.c_int(0 if is_light else 1)
        for attr in (20, 19):
            res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attr, ctypes.byref(value), ctypes.sizeof(value)
            )
            if res == 0:
                break
    except Exception as e:
        print("title bar theme failed:", e)
