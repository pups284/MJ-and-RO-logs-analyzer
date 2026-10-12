from __future__ import annotations

import re
import uuid
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QLineEdit, QMessageBox, QPlainTextEdit, QVBoxLayout,
)

from ..models import Rule
from ..platform_win import apply_dark_title_bar
from .common import section_label


class RuleFromSelectionDialog(QDialog):
    def __init__(self, parent, selected_text: str):
        super().__init__(parent)
        self.setWindowTitle("Новое правило из выделения")
        self.resize(700, 640)

        self.result_rule: Optional[Rule] = None

        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(10)

        v.addWidget(section_label("Выделенный фрагмент"))
        preview = QPlainTextEdit(selected_text[:3000])
        preview.setReadOnly(True)
        preview.setMaximumHeight(120)
        v.addWidget(preview)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self.f_name = QLineEdit()
        self.f_name.setPlaceholderText("Например: Ошибка инициализации графики")
        form.addRow("Название:", self.f_name)

        self.f_log = QComboBox()
        for x in ("any", "main", "patcher", "client", "service", "cef"):
            self.f_log.addItem(x, x)
        form.addRow("Тип лога:", self.f_log)

        self.f_sev = QComboBox()
        for x in ("error", "warning", "info"):
            self.f_sev.addItem(x, x)
        form.addRow("Важность:", self.f_sev)

        self.f_cat = QLineEdit()
        form.addRow("Категория:", self.f_cat)

        v.addLayout(form)

        v.addWidget(section_label("Что искать"))
        self.f_pattern = QPlainTextEdit()
        self.f_pattern.setPlainText(selected_text.strip())
        self.f_pattern.setMaximumHeight(110)
        v.addWidget(self.f_pattern)

        self.f_regex = QCheckBox("Считать строку регулярным выражением (blockPattern)")
        v.addWidget(self.f_regex)

        v.addWidget(section_label("Что это значит"))
        self.f_expl = QPlainTextEdit()
        v.addWidget(self.f_expl)

        v.addWidget(section_label("Что ответить игроку"))
        self.f_sugg = QPlainTextEdit()
        v.addWidget(self.f_sugg)

        v.addWidget(section_label("Ссылка на FAQ (необязательно)"))
        self.f_faq = QLineEdit()
        v.addWidget(self.f_faq)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("Создать правило")
        bb.button(QDialogButtonBox.Ok).setObjectName("Primary")
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def accept(self):
        name = self.f_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Название", "Укажите название правила.")
            return

        pattern = self.f_pattern.toPlainText().strip()
        if not pattern:
            QMessageBox.warning(self, "Что искать",
                                "Укажите текст или regex для поиска.")
            return

        is_regex = self.f_regex.isChecked()
        if is_regex:
            try:
                re.compile(pattern)
            except re.error as e:
                QMessageBox.warning(self, "Regex", f"Некорректный regex:\n{e}")
                return

        self.result_rule = Rule(
            id="custom-" + uuid.uuid4().hex[:8],
            name=name,
            log_type=self.f_log.currentData(),
            severity=self.f_sev.currentData(),
            category=self.f_cat.text().strip(),
            enabled=True,
            all_of=[] if is_regex else [pattern],
            any_of=[],
            none_of=[],
            block_pattern=pattern if is_regex else None,
            custom_check=None,
            explanation=self.f_expl.toPlainText(),
            suggestion=self.f_sugg.toPlainText(),
            faq_link=self.f_faq.text().strip(),
        )
        super().accept()

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self)