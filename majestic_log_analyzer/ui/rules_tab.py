from __future__ import annotations

import re
import uuid
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QMessageBox, QPlainTextEdit, QPushButton, QScrollArea,
    QSplitter, QVBoxLayout, QWidget,
)

from ..models import Rule
from ..storage import (
    DATA_DIR, RULES_FILE, bundled_rules_path, load_rules, save_notes, save_rules,
)

if TYPE_CHECKING:
    from .main_window import MainWindow

def _lbl(text: str, tooltip: str = "") -> QLabel:
    """Подпись поля формы. Если задан tooltip — он появится при наведении."""
    lbl = QLabel(text)
    if tooltip:
        lbl.setToolTip(tooltip)
    return lbl

class RulesTab(QWidget):
    def __init__(self, app: "MainWindow"):
        super().__init__()
        self.app = app
        self.current: Optional[Rule] = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10); outer.setSpacing(10)

        top = QHBoxLayout(); top.setSpacing(8)
        b_reload = QPushButton("Перечитать rules.json"); b_reload.setObjectName("Ghost")
        b_reload.clicked.connect(self.reload)
        b_save = QPushButton("Сохранить"); b_save.setObjectName("Primary")
        b_save.clicked.connect(self.save)
        b_new = QPushButton("Новое правило"); b_new.clicked.connect(self.new_rule)
        b_del = QPushButton("Удалить"); b_del.setObjectName("Danger")
        b_del.clicked.connect(self.del_rule)
        b_reset = QPushButton("Сбросить к bundled"); b_reset.setObjectName("Ghost")
        b_reset.clicked.connect(self.reset_to_bundled)
        b_open = QPushButton("Открыть папку с данными"); b_open.setObjectName("Ghost")
        b_open.clicked.connect(self.open_data_dir)
        top.addWidget(b_reload); top.addWidget(b_save); top.addStretch(1)
        for w in (b_new, b_del, b_reset, b_open):
            top.addWidget(w)
        outer.addLayout(top)

        split = QSplitter(Qt.Horizontal); split.setHandleWidth(8)

        self.list = QListWidget()
        self.list.itemSelectionChanged.connect(self.on_select)
        split.addWidget(self.list)

        right = QWidget()
        form = QFormLayout(right)
        form.setContentsMargins(12, 4, 12, 4)
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        self.f_id = QLineEdit(); self.f_id.setReadOnly(True)
        form.addRow(_lbl(
            "ID:",
            "Уникальный идентификатор правила.\n"
            "Используется в notes.json. Генерируется автоматически.",
        ), self.f_id)

        self.f_name = QLineEdit()
        form.addRow(_lbl(
            "Название:",
            "Как правило отображается в таблице находок и в списке слева.",
        ), self.f_name)

        self.f_log = QComboBox()
        for x in ("any", "main", "patcher", "client", "service", "cef"):
            self.f_log.addItem(x, x)
        form.addRow(_lbl(
            "Тип лога:",
            "К каким логам применяется правило.\n"
            "any — ко всем, main — только к main.log,\n"
            "client — только к client*.log и так далее.",
        ), self.f_log)

        self.f_sev = QComboBox()
        for x in ("error", "warning", "info"):
            self.f_sev.addItem(x, x)
        form.addRow(_lbl(
            "Важность:",
            "Цвет значка и приоритет находки:\n"
            "error — красный, warning — жёлтый, info — синий.",
        ), self.f_sev)

        self.f_cat = QLineEdit()
        form.addRow(_lbl(
            "Категория:",
            "Смысловая группа: Лицензия, Сеть, Патчер, Клиент и т.п.\n"
            "Показывается в колонке «Категория».",
        ), self.f_cat)

        self.f_en = QCheckBox("Включено")
        form.addRow(_lbl(
            "",
            "Если снять галку — правило не участвует в анализе,\n"
            "но остаётся в rules.json и список не пропадёт.",
        ), self.f_en)

        self.f_all = QPlainTextEdit(); self.f_all.setPlaceholderText("по одному в строке")
        form.addRow(_lbl(
            "Должны встречаться:",
            "Все эти подстроки должны присутствовать в логе, чтобы правило сработало.\n"
            "По одной на строку. Регистр не важен.\n"
            "(в rules.json — поле allOf)",
        ), self.f_all)

        self.f_any = QPlainTextEdit()
        self.f_any.setPlaceholderText("по одному в строке")
        form.addRow(_lbl(
            "Хотя бы одно из:",
            "Правило сработает, если встретится любая из этих подстрок.\n"
            "По одной на строку. Регистр не важен.\n"
            "(в rules.json — поле anyOf)",
        ), self.f_any)

        self.f_none = QPlainTextEdit()
        self.f_none.setPlaceholderText("по одному в строке")
        form.addRow(_lbl(
            "Не должно встречаться:",
            "Правило НЕ сработает, если в логе есть любая из этих подстрок.\n"
            "Удобно для отсечения ложных срабатываний.\n"
            "(в rules.json — поле noneOf)",
        ), self.f_none)

        self.f_block = QLineEdit()
        form.addRow(_lbl(
            "Regex-блок:",
            "Регулярное выражение. Если совпадает — правило срабатывает\n"
            "и подсвечивает весь найденный блок целиком.\n"
            "Ищется последнее совпадение в сессии.\n"
            "(в rules.json — поле blockPattern)",
        ), self.f_block)

        self.f_check = QLineEdit()
        form.addRow(_lbl(
            "Кастомная проверка:",
            "Имя встроенной проверки для нестандартной логики.\n"
            "Доступные: duplicate_weapon_mods, duplicate_count, sys_fileload_detail.\n"
            "(в rules.json — поле custom_check)",
        ), self.f_check)

        self.f_expl = QPlainTextEdit()
        form.addRow(_lbl(
            "Что это значит:",
            "Пояснение для вас — что означает эта ошибка.\n"
            "Показывается в правой панели при выборе находки.",
        ), self.f_expl)

        self.f_sugg = QPlainTextEdit()
        form.addRow(_lbl(
            "Что ответить:",
            "Готовая подсказка для игрока — можно выделить и скопировать.\n"
            "Показывается в правой панели при выборе находки.",
        ), self.f_sugg)

        self.f_faq = QLineEdit()
        form.addRow(_lbl(
            "FAQ:",
            "Ссылка на статью FAQ.\n"
            "Если заполнена — в панели деталей появится активная кнопка «Открыть FAQ».",
        ), self.f_faq)

        wrap = QScrollArea(); wrap.setWidgetResizable(True)
        wrap.setFrameShape(QScrollArea.NoFrame); wrap.setWidget(right)
        split.addWidget(wrap)
        split.setStretchFactor(0, 1); split.setStretchFactor(1, 3)
        split.setSizes([320, 900])
        outer.addWidget(split, 1)

        self.refresh()

    def refresh(self):
        self.list.clear()
        for r in self.app.rules:
            mark = "" if r.enabled else "   (off)"
            self.list.addItem(f"{r.name}{mark}")
            self.list.item(self.list.count() - 1).setData(Qt.UserRole, r.id)

    def select_rule(self, rule_id: str):
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole) == rule_id:
                self.list.setCurrentRow(i); return

    def on_select(self):
        items = self.list.selectedItems()
        if not items:
            return
        rid = items[0].data(Qt.UserRole)
        r = next((x for x in self.app.rules if x.id == rid), None)
        if not r:
            return
        self.current = r
        self.f_id.setText(r.id); self.f_name.setText(r.name)
        self.f_log.setCurrentText(r.log_type); self.f_sev.setCurrentText(r.severity)
        self.f_cat.setText(r.category); self.f_en.setChecked(r.enabled)
        self.f_all.setPlainText("\n".join(r.all_of))
        self.f_any.setPlainText("\n".join(r.any_of))
        self.f_none.setPlainText("\n".join(r.none_of))
        self.f_block.setText(r.block_pattern or "")
        self.f_check.setText(r.custom_check or "")
        self.f_count_pattern.setText(r.count_pattern or "")
        self.f_count_expected.setText(", ".join(str(x) for x in r.count_expected))
        self.f_expl.setPlainText(r.explanation)
        self.f_sugg.setPlainText(r.suggestion)
        self.f_faq.setText(r.faq_link)

    def _apply(self) -> bool:
        r = self.current
        if not r:
            return False

        bp = self.f_block.text().strip()
        if bp:
            try:
                re.compile(bp)
            except re.error as e:
                QMessageBox.warning(self, "Regex", f"Некорректный regex:\n{e}")
                return False

        expected: list[int] = []
        raw = self.f_count_expected.text().strip()
        if raw:
            for part in raw.split(","):
                part = part.strip()
                if not part:
                    continue
                try:
                    expected.append(int(part))
                except ValueError:
                    QMessageBox.warning(
                        self, "Числа",
                        f"«{part}» — не целое число. "
                        f"Ожидаемые количества вводятся через запятую."
                    )
                    return False

        r.name = self.f_name.text() or r.id
        r.log_type = self.f_log.currentData()
        r.severity = self.f_sev.currentData()
        r.category = self.f_cat.text()
        r.enabled = self.f_en.isChecked()
        r.all_of = [s for s in (x.strip() for x in self.f_all.toPlainText().splitlines()) if s]
        r.any_of = [s for s in (x.strip() for x in self.f_any.toPlainText().splitlines()) if s]
        r.none_of = [s for s in (x.strip() for x in self.f_none.toPlainText().splitlines()) if s]
        r.block_pattern = bp or None
        r.custom_check = self.f_check.text().strip() or None
        r.count_pattern = self.f_count_pattern.text().strip()
        r.count_expected = expected
        r.explanation = self.f_expl.toPlainText()
        r.suggestion = self.f_sugg.toPlainText()
        r.faq_link = self.f_faq.text()
        return True

    def save(self):
        if not self._apply():
            return
        save_rules(self.app.rules)
        self.refresh()
        self.app.analyze_tab.run_analysis()
        QMessageBox.information(self, "Сохранено",
                                f"rules.json обновлён ({len(self.app.rules)} правил).")

    def reload(self):
        self.app.rules = load_rules()
        self.refresh()
        self.app.analyze_tab.run_analysis()

    def new_rule(self):
        rid = "custom-" + uuid.uuid4().hex[:8]
        self.app.rules.append(Rule(id=rid, name="Новое правило"))
        save_rules(self.app.rules); self.refresh(); self.select_rule(rid)

    def del_rule(self):
        if not self.current:
            return
        if QMessageBox.question(
            self, "Удалить",
            f"Удалить правило «{self.current.name}»?\n"
            f"Все примечания этого правила тоже будут удалены."
        ) != QMessageBox.Yes:
            return
        rid = self.current.id
        self.app.rules = [r for r in self.app.rules if r.id != rid]
        self.app.notes = [n for n in self.app.notes if n.rule_id != rid]
        save_rules(self.app.rules); save_notes(self.app.notes)
        self.refresh()
        self.app.analyze_tab.run_analysis()
        self.app.notes_tab.refresh()
        self.app.update_status()

    def reset_to_bundled(self):
        if QMessageBox.question(
            self, "Сброс",
            "Перезаписать rules.json bundled-версией?\n"
            "Все пользовательские правила и примечания будут удалены."
        ) != QMessageBox.Yes:
            return
        src = bundled_rules_path()
        if not src.exists():
            QMessageBox.warning(self, "Ошибка", "bundled_rules.json не найден.")
            return
        RULES_FILE.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        self.app.rules = load_rules()
        self.app.notes = []
        save_notes(self.app.notes)
        self.refresh()
        self.app.analyze_tab.run_analysis()
        self.app.notes_tab.refresh()
        self.app.update_status()

    def open_data_dir(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(DATA_DIR)))