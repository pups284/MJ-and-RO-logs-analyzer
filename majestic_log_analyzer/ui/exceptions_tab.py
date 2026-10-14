from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..storage import load_notes, save_notes

if TYPE_CHECKING:
    from .main_window import MainWindow


class ExceptionsTab(QWidget):
    def __init__(self, app: "MainWindow"):
        super().__init__()
        self.app = app

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10); outer.setSpacing(8)

        top = QHBoxLayout(); top.setSpacing(6)
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
            "Исключения скрывают находки из основной таблицы. "
            "Убираются отсюда или из вкладки «Анализ → Скрытые»."
        )
        hint.setObjectName("DetailMeta")
        hint.setWordWrap(True)
        outer.addWidget(hint)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Правило", "Заголовок", "Сигнатура", "Создано"]
        )
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        h.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        outer.addWidget(self.table, 1)

        self.refresh()

    def refresh(self):
        self.table.setRowCount(0)
        for n in self.app.notes:
            if n.kind != "ignore":
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            rule = next((r for r in self.app.rules if r.id == n.rule_id), None)
            it0 = QTableWidgetItem(rule.name if rule else n.rule_id)
            it0.setData(Qt.UserRole, n.id)
            self.table.setItem(row, 0, it0)
            self.table.setItem(row, 1, QTableWidgetItem(n.title))
            sig = QTableWidgetItem(n.signature[:140])
            sig.setForeground(QColor("#8b94a3"))
            self.table.setItem(row, 2, sig)
            self.table.setItem(row, 3, QTableWidgetItem((n.created_at or "")[:19]))

    def reload(self):
        self.app.notes = load_notes()
        self.refresh()
        self.app.analyze_tab.run_analysis()
        self.app.update_status()

    def save(self):
        save_notes(self.app.notes)
        QMessageBox.information(self, "Сохранено", "notes.json обновлён.")

    def del_selected(self):
        rows = sorted({ix.row() for ix in self.table.selectedIndexes()})
        if not rows:
            return
        ids = {self.table.item(r, 0).data(Qt.UserRole)
               for r in rows if self.table.item(r, 0)}
        if not ids:
            return
        if QMessageBox.question(self, "Удалить",
                                f"Снять {len(ids)} исключений?") != QMessageBox.Yes:
            return
        self.app.notes = [n for n in self.app.notes if n.id not in ids]
        save_notes(self.app.notes)
        self.refresh()
        self.app.analyze_tab.run_analysis()
        self.app.update_status()