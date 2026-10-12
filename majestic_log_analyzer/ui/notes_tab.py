from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QHBoxLayout, QHeaderView, QLabel, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..analysis import find_duplicate_note
from ..storage import load_notes, save_notes
from .note_dialog import NoteDialog

if TYPE_CHECKING:
    from .main_window import MainWindow


class NotesTab(QWidget):
    def __init__(self, app: "MainWindow"):
        super().__init__()
        self.app = app

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10); outer.setSpacing(10)

        top = QHBoxLayout(); top.setSpacing(8)
        b_reload = QPushButton("Перечитать notes.json"); b_reload.setObjectName("Ghost")
        b_reload.clicked.connect(self.reload)
        b_save = QPushButton("Сохранить"); b_save.setObjectName("Primary")
        b_save.clicked.connect(self.save)
        b_edit = QPushButton("Редактировать"); b_edit.setObjectName("Ghost")
        b_edit.clicked.connect(self.edit_selected)
        b_del = QPushButton("Удалить выбранное"); b_del.setObjectName("Danger")
        b_del.clicked.connect(self.del_selected)
        top.addWidget(b_reload); top.addWidget(b_save)
        top.addStretch(1); top.addWidget(b_edit); top.addWidget(b_del)
        outer.addLayout(top)

        hint = QLabel(
            "Двойной клик по строке — редактирование. "
            "Ctrl/Shift — множественный выбор."
        )
        hint.setObjectName("DetailMeta")
        outer.addWidget(hint)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Тип", "Правило", "Заголовок", "Сигнатура", "Создано"]
        )
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self.edit_selected)
        outer.addWidget(self.table, 1)

        self.refresh()

    def refresh(self):
        self.table.setRowCount(0)
        for n in self.app.notes:
            row = self.table.rowCount()
            self.table.insertRow(row)
            kind_label = {"ignore": "Игнор", "note": "Примечание"}.get(n.kind, n.kind)
            it0 = QTableWidgetItem(kind_label)
            it0.setData(Qt.UserRole, n.id)
            self.table.setItem(row, 0, it0)
            rule = next((r for r in self.app.rules if r.id == n.rule_id), None)
            self.table.setItem(row, 1, QTableWidgetItem(rule.name if rule else n.rule_id))
            self.table.setItem(row, 2, QTableWidgetItem(n.title))
            sig = QTableWidgetItem(n.signature[:140])
            sig.setForeground(QColor("#8b94a3"))
            self.table.setItem(row, 3, sig)
            self.table.setItem(row, 4, QTableWidgetItem((n.created_at or "")[:19]))

    def reload(self):
        self.app.notes = load_notes()
        self.refresh()
        self.app.analyze_tab.run_analysis()
        self.app.update_status()

    def save(self):
        save_notes(self.app.notes)
        QMessageBox.information(self, "Сохранено", "notes.json обновлён.")

    def _selected_note(self):
        rows = sorted({ix.row() for ix in self.table.selectedIndexes()})
        if not rows:
            return None
        it = self.table.item(rows[0], 0)
        if not it:
            return None
        nid = it.data(Qt.UserRole)
        return next((n for n in self.app.notes if n.id == nid), None)

    def edit_selected(self):
        note = self._selected_note()
        if not note:
            return
        dlg = NoteDialog(self, existing=note)
        if dlg.exec() != QDialog.Accepted or not dlg.result_note:
            return
        # проверка на дубликат (исключая саму себя)
        dup = find_duplicate_note(
            self.app.notes, note.rule_id, note.signature, note.kind,
            exclude_id=note.id,
        )
        if dup:
            QMessageBox.information(
                self, "Дубликат",
                "Уже есть другая запись с таким же правилом, сигнатурой и типом."
            )
            # откатывать изменения не станем — пользователь мог изменить
            # заголовок/комментарий и хочет их сохранить, просто тип/подпись
            # совпадают с другой записью.
        save_notes(self.app.notes)
        self.refresh()
        self.app.analyze_tab.run_analysis()
        self.app.update_status()

    def del_selected(self):
        rows = sorted({ix.row() for ix in self.table.selectedIndexes()})
        if not rows:
            return
        ids = {self.table.item(r, 0).data(Qt.UserRole)
               for r in rows if self.table.item(r, 0)}
        if not ids:
            return
        if QMessageBox.question(self, "Удалить",
                                f"Удалить {len(ids)} записей?") != QMessageBox.Yes:
            return
        self.app.notes = [n for n in self.app.notes if n.id not in ids]
        save_notes(self.app.notes)
        self.refresh()
        self.app.analyze_tab.run_analysis()
        self.app.update_status()