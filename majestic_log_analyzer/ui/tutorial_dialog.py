from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout
)

from ..style import SPACE
from .common import apply_shadow


class TutorialPopup(QDialog):
    next_clicked = Signal()
    prev_clicked = Signal()
    skip_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(368)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame()
        self.card.setObjectName("TutorialCard")
        apply_shadow(self.card, blur=42, offset=12, alpha=110)

        lay = QVBoxLayout(self.card)
        lay.setContentsMargins(SPACE["xl"], SPACE["xl"], SPACE["xl"], SPACE["xl"])
        lay.setSpacing(SPACE["md"])

        self.lbl_step = QLabel()
        self.lbl_step.setObjectName("StatCaption")

        self.lbl_title = QLabel("Обучение")
        self.lbl_title.setObjectName("DetailTitle")

        self.lbl_text = QLabel()
        self.lbl_text.setObjectName("DetailMeta")
        self.lbl_text.setWordWrap(True)
        self.lbl_text.setMinimumHeight(64)

        self.progress = QProgressBar()
        self.progress.setObjectName("TutorialProgress")
        self.progress.setTextVisible(False)
        self.progress.setRange(1, 1)
        self.progress.setValue(1)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(SPACE["sm"])
        self.btn_skip = QPushButton("Пропустить")
        self.btn_skip.setObjectName("Ghost")
        self.btn_skip.clicked.connect(self.skip_clicked.emit)

        self.btn_back = QPushButton("Назад")
        self.btn_back.clicked.connect(self.prev_clicked.emit)

        self.btn_next = QPushButton("Далее")
        self.btn_next.setObjectName("Primary")
        self.btn_next.clicked.connect(self.next_clicked.emit)

        btn_row.addWidget(self.btn_skip)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_back)
        btn_row.addWidget(self.btn_next)

        lay.addWidget(self.lbl_step)
        lay.addWidget(self.lbl_title)
        lay.addWidget(self.lbl_text)
        lay.addWidget(self.progress)
        lay.addSpacing(SPACE["xs"])
        lay.addLayout(btn_row)

        self.layout.addWidget(self.card)

    def set_step(self, title: str, text: str, step: int, total: int):
        self.lbl_title.setText(title)
        self.lbl_text.setText(text)
        self.lbl_step.setText(f"ШАГ {step} ИЗ {total}")
        self.progress.setRange(1, max(1, total))
        self.progress.setValue(step)
        self.btn_back.setVisible(step > 1)
        if step == total:
            self.btn_next.setText("Завершить")
        else:
            self.btn_next.setText("Далее")

        animation = QPropertyAnimation(self, b"windowOpacity", self)
        animation.setDuration(140)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start()
        self._fade_animation = animation
