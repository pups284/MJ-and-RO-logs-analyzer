from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox, QPlainTextEdit, QPushButton,
    QSplitter, QVBoxLayout, QWidget,
)

from ..models import Note
from ..storage import load_notes, save_notes
from .common import section_label

if TYPE_CHECKING:
    from .main_window import MainWindow


class NotesTab(QWidget):
    def __init__(self, app: "MainWindow"):
        super().__init__()
        self.app = app
        self.current: Optional[Note] = None
        self._loading = False
        self._dirty = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(6)
        b_reload = QPushButton("Перечитать notes.json"); b_reload.setObjectName("Ghost")
        b_reload.clicked.connect(self.reload)
        b_save = QPushButton("Сохранить"); b_save.setObjectName("Primary")
        b_save.clicked.connect(self.save)
        b_del = QPushButton("Удалить выбранные"); b_del.setObjectName("Danger")
        b_del.clicked.connect(self.del_selected)

        top.addWidget(b_reload)
        top.addWidget(b_save)
        top.addStretch(1)
        top.addWidget(b_del)
        outer.addLayout(top)

        hint = QLabel(
            "Примечания — любые записи к правилам и их сигнатурам. "
            "Можно создать несколько к одной сигнатуре. "
            "Исключения живут в отдельной вкладке."
        )
        hint.setObjectName("DetailMeta")
        hint.setWordWrap(True)
        outer.addWidget(hint)

        split = QSplitter(Qt.Horizontal)
        split.setHandleWidth(8)

        self.list = QListWidget()
        self.list.setObjectName("NotesList")
        self.list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list.itemSelectionChanged.connect(self.on_select)
        split.addWidget(self.list)

        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(12, 0, 0, 0)
        rv.setSpacing(6)

        self.lbl_rule = QLabel("—")
        self.lbl_rule.setObjectName("DetailTitle")
        self.lbl_rule.setWordWrap(True)

        self.lbl_sig = QLabel("—")
        self.lbl_sig.setObjectName("DetailMeta")
        self.lbl_sig.setWordWrap(True)
        self.lbl_sig.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.lbl_created = QLabel("")
        self.lbl_created.setObjectName("DetailMeta")

        rv.addWidget(section_label("Правило"))
        rv.addWidget(self.lbl_rule)
        rv.addWidget(section_label("Сигнатура"))
        rv.addWidget(self.lbl_sig)
        rv.addWidget(self.lbl_created)
        rv.addSpacing(4)

        rv.addWidget(section_label("Заголовок"))
        self.title_edit = QLineEdit()
        self.title_edit.textChanged.connect(self._on_edit)
        rv.addWidget(self.title_edit)

        rv.addWidget(section_label("Комментарий"))
        self.comment_edit = QPlainTextEdit()
        self.comment_edit.textChanged.connect(self._on_edit)
        rv.addWidget(self.comment_edit, 1)

        self.status_lbl = QLabel("")
        self.status_lbl.setObjectName("DetailMeta")
        rv.addWidget(self.status_lbl)

        split.addWidget(right)
        split.setStretchFactor(0, 2)
        split.setStretchFactor(1, 3)
        split.setSizes([380, 720])
        outer.addWidget(split, 1)

        self.refresh()

    # ── список ──
    def refresh(self):
        prev_id = self.current.id if self.current else None
        self.list.blockSignals(True)
        self.list.clear()
        for n in self.app.notes:
            if n.kind != "note":
                continue
            rule = next((r for r in self.app.rules if r.id == n.rule_id), None)
            rule_label = rule.name if rule else n.rule_id
            title = n.title or "(без заголовка)"
            item = QListWidgetItem(f"{title}   ·   {rule_label}")
            item.setData(Qt.UserRole, n.id)
            item.setToolTip(n.comment or n.preview or "")
            self.list.addItem(item)
        self.list.blockSignals(False)

        if prev_id:
            for i in range(self.list.count()):
                if self.list.item(i).data(Qt.UserRole) == prev_id:
                    self.list.setCurrentRow(i)
                    return
        self._clear_form()

    def _selected_ids(self) -> list[str]:
        return [it.data(Qt.UserRole) for it in self.list.selectedItems()]

    def on_select(self):
        ids = self._selected_ids()
        if not ids:
            self._clear_form()
            return
        nid = ids[0]
        n = next((x for x in self.app.notes if x.id == nid), None)
        if not n:
            self._clear_form()
            return

        self.current = n
        self._loading = True
        rule = next((r for r in self.app.rules if r.id == n.rule_id), None)
        self.lbl_rule.setText(rule.name if rule else n.rule_id)
        self.lbl_sig.setText(n.signature or "—")
        self.lbl_created.setText(f"Создано: {(n.created_at or '')[:19]}")
        self.title_edit.setText(n.title)
        self.comment_edit.setPlainText(n.comment)
        self._loading = False
        self._dirty = False
        self.status_lbl.setText("")

    def _clear_form(self):
        self.current = None
        self._loading = True
        self.lbl_rule.setText("—")
        self.lbl_sig.setText("—")
        self.lbl_created.setText("")
        self.title_edit.setText("")
        self.comment_edit.setPlainText("")
        self._loading = False
        self._dirty = False
        self.status_lbl.setText("")

    def _on_edit(self):
        if self._loading or not self.current:
            return
        self.current.title = self.title_edit.text()
        self.current.comment = self.comment_edit.toPlainText()
        self._dirty = True
        self.status_lbl.setText("• есть несохранённые изменения")

        # обновим первую строку в списке на лету
        cur_id = self.current.id
        for i in range(self.list.count()):
            it = self.list.item(i)
            if it.data(Qt.UserRole) == cur_id:
                rule = next((r for r in self.app.rules if r.id == self.current.rule_id), None)
                rule_label = rule.name if rule else self.current.rule_id
                title = self.current.title or "(без заголовка)"
                it.setText(f"{title}   ·   {rule_label}")
                break

    # ── кнопки ──
    def reload(self):
        if self._dirty and QMessageBox.question(
            self, "Не сохранено",
            "В текущем примечании есть несохранённые изменения. Перечитать?"
        ) != QMessageBox.Yes:
            return
        self.app.notes = load_notes()
        self.refresh()
        self.app.analyze_tab.run_analysis()
        self.app.update_status()

    def save(self):
        save_notes(self.app.notes)
        self._dirty = False
        self.status_lbl.setText("Сохранено")
        self.app.analyze_tab.run_analysis()
        self.app.update_status()

    def del_selected(self):
        ids = self._selected_ids()
        if not ids:
            return
        if QMessageBox.question(
            self, "Удалить",
            f"Удалить {len(ids)} примечаний?"
        ) != QMessageBox.Yes:
            return
        id_set = set(ids)
        self.app.notes = [n for n in self.app.notes if n.id not in id_set]
        save_notes(self.app.notes)
        self._dirty = False
        self.refresh()
        self.app.analyze_tab.run_analysis()
        self.app.update_status()