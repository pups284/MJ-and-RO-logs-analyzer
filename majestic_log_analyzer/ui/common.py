from __future__ import annotations

from PySide6.QtWidgets import QLabel


def section_label(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setObjectName("SectionLabel")
    return lbl