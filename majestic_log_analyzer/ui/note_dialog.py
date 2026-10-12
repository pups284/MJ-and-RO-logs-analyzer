from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel,
    QLineEdit, QPlainTextEdit, QTextEdit, QVBoxLayout,
)

from ..models import Finding, Note
from ..platform_win import apply_dark_title_bar
from .common import section_label


class NoteDialog(QDialog):
    """Создаёт новую заметку (если передан finding) или редактирует
    существующую (если передан existing)."""

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
        self.resize(640, 580)

        # Что показывать как контекст
        if existing:
            rule_id = existing.rule_id
            signature = existing.signature
            preview_text = existing.preview or "—"
        else:
            rule_id = finding.rule_id
            signature = finding.signature
            preview_text = finding.context[:2000]

        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(10)

        v.addWidget(section_label("Правило"))
        v.addWidget(QLabel(rule_id))

        v.addWidget(section_label("Сигнатура"))
        sig = QLabel(signature[:200] or "—")
        sig.setObjectName("DetailMeta")
        sig.setWordWrap(True)
        v.addWidget(sig)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self.kind_cb = QComboBox()
        self.kind_cb.addItem("Примечание (не скрывать)", "note")
        self.kind_cb.addItem("Игнорировать (скрыть находку)", "ignore")
        form.addRow("Тип:", self.kind_cb)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Коротко, для таблицы")
        form.addRow("Заголовок:", self.title_edit)
        v.addLayout(form)

        v.addWidget(section_label("Комментарий"))
        self.comment = QTextEdit()
        v.addWidget(self.comment, 1)

        v.addWidget(section_label("Превью (то, что было в логе)"))
        self.preview = QPlainTextEdit(preview_text)
        self.preview.setReadOnly(True)
        self.preview.setMaximumHeight(140)
        v.addWidget(self.preview)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setObjectName("Primary")
        bb.button(QDialogButtonBox.Ok).setText("Сохранить")
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)

        # Предзаполнение при редактировании
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
            # Обновляем существующую заметку на месте
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
                created_at=datetime.utcnow().isoformat() + "Z",
            )
        super().accept()

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self)