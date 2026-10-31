from __future__ import annotations

import re
import uuid
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QScrollArea, QVBoxLayout,
    QWidget,
)

from ..models import Rule
from ..platform_win import apply_dark_title_bar
from ..style import SPACE
from .common import section_label


class RuleFromSelectionDialog(QDialog):
    def __init__(self, parent, selected_text: str):
        super().__init__(parent)
        self.setWindowTitle("Новое правило из выделения")
        app = QApplication.instance()
        if app and not app.windowIcon().isNull():
            self.setWindowIcon(app.windowIcon())
        self.resize(720, 700)

        self.result_rule: Optional[Rule] = None

        v = QVBoxLayout(self)
        v.setContentsMargins(SPACE["xl"], SPACE["xl"], SPACE["xl"], SPACE["xl"])
        v.setSpacing(SPACE["md"])

        title = QLabel("Новое правило из выделения")
        title.setObjectName("DialogTitle")
        subtitle = QLabel("Проверьте фрагмент и задайте параметры поиска.")
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

        cv.addWidget(section_label("Выделенный фрагмент"))
        preview = QPlainTextEdit(selected_text[:3000])
        preview.setReadOnly(True)
        preview.setMinimumHeight(90)
        preview.setMaximumHeight(120)
        cv.addWidget(preview)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form.setHorizontalSpacing(SPACE["lg"])
        form.setVerticalSpacing(SPACE["sm"])
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

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

        cv.addLayout(form)

        cv.addWidget(section_label("Что искать"))
        self.f_pattern = QPlainTextEdit()
        self.f_pattern.setPlainText(selected_text.strip())
        self.f_pattern.setMinimumHeight(80)
        self.f_pattern.setMaximumHeight(110)
        cv.addWidget(self.f_pattern)

        self.f_regex = QCheckBox("Считать строку регулярным выражением (blockPattern)")
        cv.addWidget(self.f_regex)

        cv.addWidget(section_label("Что это значит"))
        self.f_expl = QPlainTextEdit()
        self.f_expl.setPlaceholderText("Объяснение причины ошибки")
        self.f_expl.setMinimumHeight(70)
        cv.addWidget(self.f_expl)

        cv.addWidget(section_label("Что ответить игроку"))
        self.f_sugg = QPlainTextEdit()
        self.f_sugg.setPlaceholderText("Готовый текст ответа игроку")
        self.f_sugg.setMinimumHeight(70)
        cv.addWidget(self.f_sugg)

        cv.addWidget(section_label("Ссылка на FAQ (необязательно)"))
        self.f_faq = QLineEdit()
        cv.addWidget(self.f_faq)

        scroll.setWidget(content)
        v.addWidget(scroll, 1)

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