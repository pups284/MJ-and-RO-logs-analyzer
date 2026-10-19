from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
)


class TutorialPopup(QDialog):
    next_clicked = Signal()
    prev_clicked = Signal()
    skip_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(340)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame()
        self.card.setObjectName("HeaderBar")
        self.card.setStyleSheet("QFrame#HeaderBar { border-radius: 12px; padding: 16px; }")
        
        lay = QVBoxLayout(self.card)
        lay.setSpacing(10)

        self.lbl_title = QLabel("Обучение")
        self.lbl_title.setObjectName("DetailTitle")
        
        self.lbl_text = QLabel()
        self.lbl_text.setObjectName("DetailMeta")
        self.lbl_text.setWordWrap(True)
        self.lbl_text.setMinimumHeight(60)
        
        self.lbl_step = QLabel()
        self.lbl_step.setObjectName("DetailMeta")
        self.lbl_step.setStyleSheet("font-size: 11px;")
        
        btn_row = QHBoxLayout()
        self.btn_skip = QPushButton("Пропустить")
        self.btn_skip.setObjectName("Ghost")
        self.btn_skip.clicked.connect(self.skip_clicked.emit)
        
        self.btn_back = QPushButton("← Назад")
        self.btn_back.clicked.connect(self.prev_clicked.emit)
        
        self.btn_next = QPushButton("Далее →")
        self.btn_next.setObjectName("Primary")
        self.btn_next.clicked.connect(self.next_clicked.emit)
        
        btn_row.addWidget(self.btn_skip)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_back)
        btn_row.addWidget(self.btn_next)
        
        lay.addWidget(self.lbl_title)
        lay.addWidget(self.lbl_text)
        lay.addWidget(self.lbl_step)
        lay.addSpacing(10)
        lay.addLayout(btn_row)
        
        self.layout.addWidget(self.card)

    def set_step(self, title: str, text: str, step: int, total: int):
        self.lbl_title.setText(title)
        self.lbl_text.setText(text)
        self.lbl_step.setText(f"Шаг {step} из {total}")
        self.btn_back.setVisible(step > 1)
        if step == total:
            self.btn_next.setText("Завершить")
        else:
            self.btn_next.setText("Далее →")