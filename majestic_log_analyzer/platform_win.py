from __future__ import annotations
import sys


def apply_dark_title_bar(widget) -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        hwnd = int(widget.winId())
        value = ctypes.c_int(1)
        for attr in (20, 19):
            res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attr, ctypes.byref(value), ctypes.sizeof(value)
            )
            if res == 0:
                break
    except Exception as e:
        print("dark title bar failed:", e)