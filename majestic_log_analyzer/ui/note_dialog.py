from __future__ import annotations

import uuid
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel,
    QLineEdit, QPlainTextEdit, QScrollArea, QTextEdit, QVBoxLayout, QWidget,
)

from ..models import Finding, Note, utc_now_iso
from ..platform_win import apply_dark_title_bar
from ..style import SPACE
from .common import section_label


class NoteDialog(QDialog):
    def __init__(
        self,
        parent,
        finding: Optional[Finding] = None,
        existing: Optional[Note] = None,
    ):
        super().__init__(parent)
        if finding is None and existing is None:
            raise ValueError("Нужен либо finding, либо existing note")

        self.finding = finding
        self.existing = existing

        self.setWindowTitle("Редактирование записи" if existing else "Примечание")
        app = QApplication.instance()
        if app and not app.windowIcon().isNull():
            self.setWindowIcon(app.windowIcon())
        self.resize(640, 580)

        if existing:
            rule_id = existing.rule_id
            signature = existing.signature
            preview_text = existing.preview or "—"
        else:
            rule_id = finding.rule_id
            signature = finding.signature
            preview_text = finding.context[:2000]

        v = QVBoxLayout(self)
        v.setContentsMargins(SPACE["xl"], SPACE["xl"], SPACE["xl"], SPACE["xl"])
        v.setSpacing(SPACE["md"])

        title = QLabel("Редактирование записи" if existing else "Примечание к находке")
        title.setObjectName("DialogTitle")
        subtitle = QLabel("Заметка сохраняется локально и не меняет правило.")
        subtitle.setObjectName("DialogSubtitle")
        v.addWidget(title)
        v.addWidget(subtitle)
        v.addSpacing(SPACE["xs"])

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        content = QWidget()
        cv = QVBoxLayout(content)
        cv.setContentsMargins(0, 0, SPACE["sm"], 0)
        cv.setSpacing(SPACE["sm"])

        cv.addWidget(section_label("Правило"))
        cv.addWidget(QLabel(rule_id))

        cv.addWidget(section_label("Сигнатура"))
        sig = QLabel(signature[:200] or "—")
        sig.setObjectName("DetailMeta")
        sig.setWordWrap(True)
        cv.addWidget(sig)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form.setHorizontalSpacing(SPACE["lg"])
        form.setVerticalSpacing(SPACE["sm"])
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.kind_cb = QComboBox()
        self.kind_cb.addItem("Примечание (не скрывать)", "note")
        self.kind_cb.addItem("Игнорировать (скрыть находку)", "ignore")
        form.addRow("Тип:", self.kind_cb)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Коротко, для таблицы")
        form.addRow("Заголовок:", self.title_edit)
        cv.addLayout(form)

        cv.addWidget(section_label("Комментарий"))
        self.comment = QTextEdit()
        self.comment.setMinimumHeight(150)
        cv.addWidget(self.comment)

        cv.addWidget(section_label("Превью (то, что было в логе)"))
        self.preview = QPlainTextEdit(preview_text)
        self.preview.setReadOnly(True)
        self.preview.setMinimumHeight(110)
        self.preview.setMaximumHeight(150)
        cv.addWidget(self.preview)

        scroll.setWidget(content)
        v.addWidget(scroll, 1)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setObjectName("Primary")
        bb.button(QDialogButtonBox.Ok).setText("Сохранить")
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)

        if existing:
            idx = self.kind_cb.findData(existing.kind)
            if idx >= 0:
                self.kind_cb.setCurrentIndex(idx)
            self.title_edit.setText(existing.title)
            self.comment.setPlainText(existing.comment)

        self.result_note: Optional[Note] = None

    def accept(self):
        kind = self.kind_cb.currentData()
        title = self.title_edit.text().strip()

        if self.existing:
            self.existing.kind = kind
            self.existing.title = title or self.existing.title
            self.existing.comment = self.comment.toPlainText()
            self.result_note = self.existing
        else:
            fallback_title = (
                title
                or f"{'Игнор' if kind == 'ignore' else 'Примечание'}: "
                   f"{self.finding.rule_name}"
            )
            self.result_note = Note(
                id="note-" + uuid.uuid4().hex[:10],
                rule_id=self.finding.rule_id,
                signature=self.finding.signature,
                kind=kind,
                title=fallback_title,
                comment=self.comment.toPlainText(),
                preview=self.finding.context[:400],
                created_at=utc_now_iso(),
            )
        super().accept()

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self)
