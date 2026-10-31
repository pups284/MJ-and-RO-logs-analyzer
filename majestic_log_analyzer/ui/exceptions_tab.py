from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QFrame, QHBoxLayout, QHeaderView, QLabel, QMessageBox,
    QProgressDialog, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from ..github_sync import GitHubSync
from ..storage import load_notes, save_notes
from ..style import SPACE, theme_tokens
from .common import card_frame, section_label

if TYPE_CHECKING:
    from .main_window import MainWindow


class ExceptionsTab(QWidget):
    def __init__(self, app: "MainWindow"):
        super().__init__()
        self.app = app
        self.progress_dlg: Optional[QProgressDialog] = None
        self.worker: Optional[GitHubSync] = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(SPACE["lg"])

        toolbar = card_frame()
        top = QHBoxLayout(toolbar)
        top.setContentsMargins(SPACE["md"], SPACE["md"], SPACE["md"], SPACE["md"])
        top.setSpacing(SPACE["sm"])
        b_reload = QPushButton("Перечитать")
        b_reload.setObjectName("Ghost")
        b_reload.setToolTip("Перечитать exceptions.json с диска")
        b_reload.clicked.connect(self.reload)
        b_save = QPushButton("Сохранить")
        b_save.setObjectName("Primary")
        b_save.clicked.connect(self.save)
        b_github = QPushButton("Из GitHub")
        b_github.setToolTip("Обновить исключения из GitHub")
        b_github.clicked.connect(self.update_from_github)
        b_del = QPushButton("Удалить")
        b_del.setObjectName("Danger")
        b_del.setToolTip("Удалить выбранные исключения")
        b_del.clicked.connect(self.del_selected)

        top.addWidget(b_reload)
        top.addWidget(b_save)
        top.addWidget(b_github)
        top.addStretch(1)
        top.addWidget(b_del)
        outer.addWidget(toolbar)

        hint = QLabel(
            "Исключения скрывают находки из основной таблицы. "
            "Хранятся в exceptions.json. Убираются отсюда или из вкладки "
            "«Анализ → Скрытые»."
        )
        hint.setObjectName("HintBar")
        hint.setWordWrap(True)
        outer.addWidget(hint)

        table_card = card_frame()
        tc = QVBoxLayout(table_card)
        tc.setContentsMargins(
            SPACE["lg"] - 2, SPACE["lg"] - 2, SPACE["lg"] - 2, SPACE["lg"] - 2
        )
        tc.setSpacing(SPACE["sm"])
        table_head = QHBoxLayout()
        table_head.setContentsMargins(0, 0, 0, 0)
        table_head.setSpacing(SPACE["sm"])
        table_head.addWidget(section_label("Скрытые находки"))
        table_head.addStretch(1)
        self.count_lbl = QLabel("0")
        self.count_lbl.setObjectName("CountBadge")
        table_head.addWidget(self.count_lbl)
        tc.addLayout(table_head)

        self.table = QTableWidget(0, 4)
        self.table.setObjectName("FlatTable")
        self.table.setFrameShape(QFrame.NoFrame)
        self.table.setShowGrid(False)
        self.table.setHorizontalHeaderLabels(
            ["Правило", "Заголовок", "Сигнатура", "Создано"]
        )
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        h.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        h.setFixedHeight(36)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        tc.addWidget(self.table, 1)
        outer.addWidget(table_card, 1)

        self.refresh()

    def refresh(self) -> None:
        self.table.setRowCount(0)
        tokens = theme_tokens(self.app.current_theme)
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
            sig.setForeground(QColor(tokens["muted"]))
            self.table.setItem(row, 2, sig)
            self.table.setItem(row, 3, QTableWidgetItem((n.created_at or "")[:19]))
        self.count_lbl.setText(str(self.table.rowCount()))

    def apply_theme_colors(self) -> None:
        tokens = theme_tokens(self.app.current_theme)
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 2)
            if item:
                item.setForeground(QColor(tokens["muted"]))

    def reload(self) -> None:
        self.app.notes = load_notes()
        self.refresh()
        self.app.notes_tab.refresh()
        self.app.analyze_tab.run_analysis()
        self.app.update_status()

    def save(self) -> None:
        save_notes(self.app.notes)
        self.app.analyze_tab.run_analysis()
        self.app.update_status()
        QMessageBox.information(self, "Сохранено", "exceptions.json обновлён.")

    def update_from_github(self) -> None:
        if QMessageBox.question(
            self, "Обновление из GitHub",
            "Скачать актуальные исключения и объединить с локальными?\n"
            "(При совпадении приоритет будет у версии с GitHub)"
        ) != QMessageBox.Yes:
            return

        self.progress_dlg = QProgressDialog("Скачивание исключений с GitHub…", None, 0, 0, self)
        self.progress_dlg.setWindowTitle("Обновление")
        self.progress_dlg.setWindowModality(Qt.WindowModal)
        self.progress_dlg.setMinimumDuration(0)
        self.progress_dlg.setCancelButton(None)
        self.progress_dlg.show()

        self.worker = GitHubSync("exceptions", self.app.rules, self.app.notes)
        self.worker.finished.connect(self._on_github_downloaded)
        self.worker.start()

    def _on_github_downloaded(self, success: bool, error: str,
                              new_rules: list, new_notes: list) -> None:
        dlg = self.progress_dlg
        self.progress_dlg = None
        if dlg is not None:
            dlg.close()
            dlg.deleteLater()

        if not success:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить:\n{error}")
            return

        self.app.notes = new_notes
        save_notes(self.app.notes)
        self.refresh()
        self.app.notes_tab.refresh()
        self.app.analyze_tab.run_analysis()
        self.app.update_status()

        n_exc = sum(1 for n in self.app.notes if n.kind == "ignore")
        QMessageBox.information(
            self, "Готово",
            f"Исключения успешно обновлены.\nВсего исключений: {n_exc}"
        )

    def del_selected(self) -> None:
        rows = sorted({ix.row() for ix in self.table.selectedIndexes()})
        if not rows:
            return
        ids = {
            self.table.item(r, 0).data(Qt.UserRole)
            for r in rows if self.table.item(r, 0)
        }
        if not ids:
            return
        if QMessageBox.question(
            self, "Удалить", f"Снять {len(ids)} исключений?"
        ) != QMessageBox.Yes:
            return
        self.app.notes = [n for n in self.app.notes if n.id not in ids]
        save_notes(self.app.notes)
        self.refresh()
        self.app.notes_tab.refresh()
        self.app.analyze_tab.run_analysis()
        self.app.update_status()