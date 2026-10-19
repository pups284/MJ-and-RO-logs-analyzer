from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QFileDialog, QHBoxLayout, QHeaderView,
    QLabel, QListWidget, QListWidgetItem, QMenu, QMessageBox,
    QPlainTextEdit, QPushButton, QSizePolicy, QSplitter, QTabWidget,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from ..analysis import analyze, find_duplicate_note
from ..log_metadata import extract_metadata, format_metadata, short_metadata_tag
from ..models import Finding, LoadedFile, Note
from ..normalization import detect_log_type
from ..storage import save_notes, save_rules
from ..style import SEV_COLORS, SEV_MARKS
from .common import section_label
from .file_viewer import FileViewerWindow
from .note_dialog import NoteDialog
from .rule_from_selection import RuleFromSelectionDialog

if TYPE_CHECKING:
    from .main_window import MainWindow


# ─────────────────────── Константы ───────────────────────

ALLOWED_LOG_EXTENSIONS = {".log", ".txt"}


def _is_log_path(p) -> bool:
    return Path(p).suffix.lower() in ALLOWED_LOG_EXTENSIONS


# Таблица находок: [значок, правило]
COL_ICON = 0
COL_RULE = 1
COL_COUNT = 2


# ─────────────────────── Вкладка ───────────────────────

class AnalyzeTab(QWidget):
    def __init__(self, app: "MainWindow"):
        super().__init__()
        self.app = app
        self.current: Optional[Finding] = None
        self._initialized = False
        self._viewer_windows = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(10)

        # ── Верхняя панель ──
        top = QHBoxLayout()
        top.setSpacing(8)
        self.btn_load = QPushButton("Загрузить логи…")
        self.btn_load.setObjectName("Primary")
        self.btn_load.clicked.connect(self.load_files)

        btn_clear = QPushButton("Очистить")
        btn_clear.setObjectName("Ghost")
        btn_clear.clicked.connect(self.clear_files)

        btn_again = QPushButton("Переанализировать")
        btn_again.setObjectName("Ghost")
        btn_again.clicked.connect(self.run_analysis)

        top.addWidget(self.btn_load)
        top.addWidget(btn_clear)
        top.addWidget(btn_again)
        top.addStretch(1)
        outer.addLayout(top)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(8)

        # ── Левая колонка: файлы + метаданные ──
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(6)
        lv.addWidget(section_label("Файлы"))

        self.files_list = QListWidget()
        self.files_list.setMaximumWidth(360)
        self.files_list.itemSelectionChanged.connect(self._on_file_selected)
        self.files_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.files_list.customContextMenuRequested.connect(self._files_context_menu)
        self.files_list.itemDoubleClicked.connect(self._on_file_double_clicked)
        lv.addWidget(self.files_list, 1)

        self.file_info = QLabel("")
        self.file_info.setObjectName("FileInfo")
        self.file_info.setWordWrap(True)
        self.file_info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.file_info.setMinimumHeight(60)
        lv.addWidget(self.file_info)

        splitter.addWidget(left)

        # ── Центр: под-вкладки «Находки» и «Скрытые» ──
        self.middle_tabs = QTabWidget()

        # Страница «Находки»
        findings_page = QWidget()
        fp_lay = QVBoxLayout(findings_page)
        fp_lay.setContentsMargins(0, 0, 0, 0)
        fp_lay.setSpacing(6)

        self.table = QTableWidget(0, COL_COUNT)
        self.table.setHorizontalHeaderLabels(["", "Правило"])
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(COL_ICON, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(COL_RULE, QHeaderView.Stretch)
        h.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._on_findings_select)
        self.table.doubleClicked.connect(self.open_in_editor)
        fp_lay.addWidget(self.table)

        self.middle_tabs.addTab(findings_page, "Находки")

        # Страница «Скрытые»
        hidden_page = QWidget()
        hp_lay = QVBoxLayout(hidden_page)
        hp_lay.setContentsMargins(0, 0, 0, 0)
        hp_lay.setSpacing(6)

        hidden_top = QHBoxLayout()
        hidden_top.setContentsMargins(0, 0, 0, 0)
        hidden_top.setSpacing(6)

        self.hidden_info = QLabel("Скрытых находок: 0")
        self.hidden_info.setObjectName("DetailMeta")
        hidden_top.addWidget(self.hidden_info)
        hidden_top.addStretch(1)

        self.btn_restore = QPushButton("Вернуть выбранное")
        self.btn_restore.setObjectName("Ghost")
        self.btn_restore.setToolTip("Снять исключение с выделенных строк")
        self.btn_restore.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.btn_restore.clicked.connect(self.restore_hidden_selected)

        self.btn_restore_all = QPushButton("Вернуть все")
        self.btn_restore_all.setObjectName("Ghost")
        self.btn_restore_all.setToolTip("Снять все исключения")
        self.btn_restore_all.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.btn_restore_all.clicked.connect(self.restore_all_hidden)

        hidden_top.addWidget(self.btn_restore)
        hidden_top.addWidget(self.btn_restore_all)
        hp_lay.addLayout(hidden_top)

        self.hidden_table = QTableWidget(0, COL_COUNT)
        self.hidden_table.setHorizontalHeaderLabels(["", "Правило"])
        hh = self.hidden_table.horizontalHeader()
        hh.setSectionResizeMode(COL_ICON, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(COL_RULE, QHeaderView.Stretch)
        hh.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.hidden_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.hidden_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.hidden_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.hidden_table.setAlternatingRowColors(True)
        self.hidden_table.verticalHeader().setVisible(False)
        self.hidden_table.itemSelectionChanged.connect(self._on_hidden_select)
        self.hidden_table.doubleClicked.connect(self.open_in_editor)
        hp_lay.addWidget(self.hidden_table)

        self.middle_tabs.addTab(hidden_page, "Скрытые (0)")

        splitter.addWidget(self.middle_tabs)

        # ── Правая колонка: детали ──
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(8, 0, 0, 0)
        rv.setSpacing(10)

        self.detail_title = QLabel("<выберите находку>")
        self.detail_title.setObjectName("DetailTitle")
        self.detail_title.setWordWrap(True)
        rv.addWidget(self.detail_title)

        self.detail_meta = QLabel("")
        self.detail_meta.setObjectName("DetailMeta")
        self.detail_meta.setWordWrap(True)
        rv.addWidget(self.detail_meta)

        # ── Блок примечаний / исключений ──
        self.note_box = QWidget()
        nb = QVBoxLayout(self.note_box)
        nb.setContentsMargins(0, 0, 0, 0)
        nb.setSpacing(4)
        nb.addWidget(section_label("Примечания"))
        self.note_comment_edit = QPlainTextEdit()
        self.note_comment_edit.setReadOnly(True)
        self.note_comment_edit.setMaximumHeight(140)
        nb.addWidget(self.note_comment_edit)
        self.note_box.setVisible(False)
        rv.addWidget(self.note_box)

        rv.addWidget(section_label("Что нашли"))
        self.detail_context = QPlainTextEdit()
        self.detail_context.setReadOnly(True)
        self.detail_context.setMaximumHeight(170)
        rv.addWidget(self.detail_context)

        rv.addWidget(section_label("Что это значит"))
        self.detail_explanation = QTextEdit()
        self.detail_explanation.setReadOnly(True)
        self.detail_explanation.setMaximumHeight(110)
        rv.addWidget(self.detail_explanation)

        rv.addWidget(section_label("Что ответить игроку"))
        self.detail_suggestion = QTextEdit()
        self.detail_suggestion.setReadOnly(True)
        self.detail_suggestion.setMaximumHeight(110)
        rv.addWidget(self.detail_suggestion)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        self.btn_open = QPushButton("Открыть в редакторе")
        self.btn_open.setObjectName("Primary")
        self.btn_fp = QPushButton("Ложное срабатывание")
        self.btn_fp.setObjectName("Danger")
        self.btn_note = QPushButton("Добавить примечание…")
        self.btn_edit = QPushButton("Редактировать правило")
        self.btn_edit.setObjectName("Ghost")

        self.btn_open.clicked.connect(self.open_in_editor)
        self.btn_fp.clicked.connect(self.mark_false_positive)
        self.btn_note.clicked.connect(self.add_note)
        self.btn_edit.clicked.connect(self.edit_rule)

        btns.addWidget(self.btn_open)
        btns.addWidget(self.btn_fp)
        btns.addWidget(self.btn_note)
        btns.addWidget(self.btn_edit)
        btns.addStretch(1)
        rv.addLayout(btns)

        self.btn_faq = QPushButton("Открыть FAQ")
        self.btn_faq.setObjectName("Ghost")
        self.btn_faq.clicked.connect(self.open_faq)
        self.btn_faq.setEnabled(False)
        rv.addWidget(self.btn_faq)
        rv.addStretch(1)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 4)
        splitter.setStretchFactor(2, 3)
        splitter.setSizes([280, 700, 480])
        outer.addWidget(splitter, 1)

        self._initialized = True
        self.middle_tabs.currentChanged.connect(self._on_middle_tab_changed)

    # ───────── Под-вкладки ─────────
    def _on_middle_tab_changed(self, _idx: int):
        if not self._initialized:
            return
        self._clear_details()

    def _clear_details(self):
        if not hasattr(self, "detail_title"):
            return
        self.current = None
        self.detail_title.setText("<выберите находку>")
        self.detail_meta.setText("")
        self.note_box.setVisible(False)
        self.note_comment_edit.setPlainText("")
        self.detail_context.setPlainText("")
        self.detail_explanation.setPlainText("")
        self.detail_suggestion.setPlainText("")
        self.btn_faq.setEnabled(False)

    # ───────── Файлы ─────────
    def load_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Выберите логи", "",
            "Логи (*.log *.txt);;Все файлы (*)",
        )
        if paths:
            self.add_files(paths)

    def add_files(self, paths: list[str]):
        valid: list[str] = []
        rejected: list[str] = []
        for p in paths:
            if _is_log_path(p):
                valid.append(p)
            else:
                rejected.append(p)

        if rejected:
            shown = "\n".join(rejected[:10])
            more = "" if len(rejected) <= 10 else f"\n…и ещё {len(rejected) - 10}"
            QMessageBox.warning(
                self, "Это не лог",
                "Можно загружать только файлы .log или .txt.\n\n"
                f"Отклонено:\n{shown}{more}"
            )

        if not valid:
            return

        target_name = None
        skipped: list[tuple[str, str]] = []

        for p in valid:
            try:
                text = Path(p).read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                skipped.append((p, str(e)))
                continue
            name = Path(p).name
            meta = extract_metadata(name, text)
            
            # Проверяем, есть ли уже такой файл в списке
            existing = next((f for f in self.app.files if f.name == name), None)
            
            if existing:
                # Если файл уже загружен — обновляем его данные "на месте",
                # чтобы он не прыгал вниз списка
                existing.content = text
                existing.path = Path(p)
                existing.metadata = meta
            else:
                # Если файла нет — добавляем в конец
                self.app.files.append(LoadedFile(
                    name=name, content=text, path=Path(p), metadata=meta,
                ))
            
            # Запоминаем имя, чтобы в конце выделить именно его
            target_name = name

        self.refresh_files()

        # Выделяем последний обработанный файл (фокус)
        if target_name:
            self.files_list.blockSignals(True)
            for i in range(self.files_list.count()):
                if self.files_list.item(i).data(Qt.UserRole) == target_name:
                    self.files_list.setCurrentRow(i)
                    break
            self.files_list.blockSignals(False)
            self._update_file_info()

        # Перезапускаем анализ (даже если файлов не прибавилось, 
        # содержимое могло обновиться)
        if valid:
            self.run_analysis()
            
        if skipped:
            msg = "\n".join(f"{p}: {err}" for p, err in skipped[:5])
            QMessageBox.warning(self, "Некоторые файлы пропущены", msg)

    def clear_files(self):
        for win in list(self._viewer_windows.values()):
            win.close()
        self._viewer_windows.clear()

        self.app.files = []
        self.app.findings = []
        self.refresh_files()
        self.refresh_table()
        self.refresh_hidden()
        self._clear_details()
        self.app.update_status()

    def _selected_file_name(self) -> Optional[str]:
        items = self.files_list.selectedItems()
        if not items:
            return None
        return items[0].data(Qt.UserRole)

    def refresh_files(self):
        prev = self._selected_file_name()
        self.files_list.blockSignals(True)
        self.files_list.clear()
        for lf in self.app.files:
            tag = detect_log_type(lf.name)
            parts = [f"{lf.name}   [{tag}]"]
            meta_tag = short_metadata_tag(lf.metadata or {})
            if meta_tag:
                parts.append(meta_tag)
            label = "  · ".join(parts)
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, lf.name)
            tooltip = format_metadata(lf.metadata or {})
            if tooltip:
                item.setToolTip(tooltip)
            self.files_list.addItem(item)
        if prev:
            for i in range(self.files_list.count()):
                if self.files_list.item(i).data(Qt.UserRole) == prev:
                    self.files_list.setCurrentRow(i)
                    break
        self.files_list.blockSignals(False)
        self._update_file_info()

    def _update_file_info(self):
        name = self._selected_file_name()
        if not name:
            self.file_info.setText("")
            return
        lf = next((f for f in self.app.files if f.name == name), None)
        if not lf:
            self.file_info.setText("")
            return
        text = format_metadata(lf.metadata or {})
        self.file_info.setText(text or "(метаданные не найдены)")

    def _on_file_selected(self):
        self._clear_details()
        self.refresh_table()
        self.refresh_hidden()
        self._update_file_info()

    def _on_file_double_clicked(self, item):
        name = item.data(Qt.UserRole)
        lf = next((f for f in self.app.files if f.name == name), None)
        if lf:
            self._open_file_in_editor(lf)

    # ───────── Контекстное меню файла ─────────
    def _files_context_menu(self, pos):
        import subprocess
        import sys

        item = self.files_list.itemAt(pos)
        if not item:
            return
        name = item.data(Qt.UserRole)
        lf = next((f for f in self.app.files if f.name == name), None)
        if not lf:
            return

        has_path = bool(lf.path and lf.path.exists())

        menu = QMenu(self)
        act_folder = menu.addAction("Открыть в проводнике")
        act_editor = menu.addAction("Открыть в редакторе")
        menu.addSeparator()
        act_copy_path = menu.addAction("Скопировать путь")
        act_delete = menu.addAction("Удалить из списка")

        act_folder.setEnabled(has_path)
        act_editor.setEnabled(True)
        act_copy_path.setEnabled(has_path)

        chosen = menu.exec(self.files_list.viewport().mapToGlobal(pos))
        if chosen is act_folder:
            self._reveal_in_explorer(lf.path)
        elif chosen is act_editor:
            self._open_file_in_editor(lf)
        elif chosen is act_copy_path:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(str(lf.path))
        elif chosen is act_delete:
            self._remove_file(lf)

    def _reveal_in_explorer(self, path: Path):
        import subprocess
        import sys
        try:
            if sys.platform == "win32":
                subprocess.Popen(["explorer", "/select,", str(path)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", str(path)])
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))
        except Exception as e:
            QMessageBox.warning(self, "Ошибка",
                                f"Не удалось открыть проводник:\n{e}")

    def _open_file_in_editor(self, lf: LoadedFile):
        self._show_viewer(lf.name, lf.content, 0, 0)

    def _remove_file(self, lf: LoadedFile):
        if QMessageBox.question(
            self, "Удалить файл",
            f"Убрать «{lf.name}» из списка?"
        ) != QMessageBox.Yes:
            return

        # Закрываем редактор, если он открыт
        if lf.name in self._viewer_windows:
            win = self._viewer_windows.pop(lf.name)
            win.close()
                
        self.app.files = [f for f in self.app.files if f is not lf]
        if self.current and self.current.file_name == lf.name:
            self._clear_details()
        self.refresh_files()
        self.run_analysis()

    # ───────── Анализ ─────────
    def run_analysis(self):
        prev_key = None
        if self.current:
            prev_key = (self.current.rule_id,
                        self.current.file_name,
                        self.current.signature)

        pairs = [(lf.name, lf.content) for lf in self.app.files]
        self.app.findings = analyze(pairs, self.app.rules, self.app.notes)
        self.refresh_table()
        self.refresh_hidden()

        if prev_key:
            self._restore_selection(prev_key)

        self.app.update_status()

    def _restore_selection(self, key: tuple):
        for row in range(self.table.rowCount()):
            it = self.table.item(row, COL_ICON)
            if not it:
                continue
            fid = it.data(Qt.UserRole)
            f = next((x for x in self.app.findings if id(x) == fid), None)
            if f and (f.rule_id, f.file_name, f.signature) == key:
                self.table.selectRow(row)
                self.table.scrollToItem(it, QAbstractItemView.PositionAtCenter)
                return
        self._clear_details()

    def _filtered(self, items: list[Finding]) -> list[Finding]:
        fname = self._selected_file_name()
        if fname is None:
            return items
        return [f for f in items if f.file_name == fname]

    def refresh_table(self):
        self.table.setRowCount(0)
        visible = [f for f in self.app.findings if not f.is_hidden]
        visible = self._filtered(visible)
        order = {"error": 0, "warning": 1, "info": 2}
        visible.sort(key=lambda f: (order.get(f.severity, 9), f.rule_name))

        for f in visible:
            row = self.table.rowCount()
            self.table.insertRow(row)

            it_icon = QTableWidgetItem(SEV_MARKS.get(f.severity, "•"))
            it_icon.setData(Qt.UserRole, id(f))
            it_icon.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, COL_ICON, it_icon)

            self.table.setItem(row, COL_RULE, QTableWidgetItem(f.rule_name))

    def refresh_hidden(self):
        self.hidden_table.setRowCount(0)
        hidden = [f for f in self.app.findings if f.is_hidden]
        hidden = self._filtered(hidden)
        order = {"error": 0, "warning": 1, "info": 2}
        hidden.sort(key=lambda f: (order.get(f.severity, 9), f.rule_name))

        for f in hidden:
            row = self.hidden_table.rowCount()
            self.hidden_table.insertRow(row)

            sev = QTableWidgetItem(SEV_MARKS.get(f.severity, "•"))
            sev.setData(Qt.UserRole, id(f))
            sev.setTextAlignment(Qt.AlignCenter)
            self.hidden_table.setItem(row, COL_ICON, sev)

            self.hidden_table.setItem(row, COL_RULE,
                                      QTableWidgetItem(f.rule_name))

        self.middle_tabs.setTabText(1, f"Скрытые ({len(hidden)})")
        self.hidden_info.setText(f"Скрытых находок: {len(hidden)}")
        self.btn_restore.setEnabled(bool(hidden))
        self.btn_restore_all.setEnabled(bool(hidden))

    # ───────── Выбор ─────────
    def _on_findings_select(self):
        items = self.table.selectedItems()
        if not items:
            return
        row = items[0].row()
        it = self.table.item(row, COL_ICON)
        if not it:
            return
        fid = it.data(Qt.UserRole)
        f = next((x for x in self.app.findings if id(x) == fid), None)
        if f:
            self._show_finding(f)

    def _on_hidden_select(self):
        items = self.hidden_table.selectedItems()
        if not items:
            return
        it = self.hidden_table.item(items[0].row(), COL_ICON)
        if not it:
            return
        fid = it.data(Qt.UserRole)
        f = next((x for x in self.app.findings if id(x) == fid), None)
        if f:
            self._show_finding(f)

    def _show_finding(self, f: Finding):
        self.current = f
        self.detail_title.setText(f.rule_name)
        meta = f"{f.file_name}  ·  {f.severity}  ·  {f.category or '—'}"
        self.detail_meta.setText(meta)

        # ── блок примечаний ──
        if f.notes:
            parts: list[str] = []
            for n in f.notes:
                kind_label = "Исключение" if n.kind == "ignore" else "Примечание"
                title = n.title or kind_label
                block = f"{kind_label}: {title}"
                if n.comment:
                    block += f"\n{n.comment}"
                parts.append(block)
            self.note_comment_edit.setPlainText(
                "\n\n──────────\n\n".join(parts)
            )
            self.note_box.setVisible(True)
        else:
            self.note_box.setVisible(False)
            self.note_comment_edit.setPlainText("")

        self.detail_context.setPlainText(f.context)
        self.detail_explanation.setPlainText(f.explanation)
        self.detail_suggestion.setPlainText(f.suggestion)
        self.btn_faq.setEnabled(bool(f.faq_link))

    def open_faq(self):
        if self.current and self.current.faq_link:
            QDesktopServices.openUrl(QUrl(self.current.faq_link))

    # ───────── Открыть в редакторе ─────────
    def open_in_editor(self):
        f = self.current
        if f:
            file_name = f.file_name
            pos = f.file_pos
            length = f.file_match_len
        else:
            file_name = self._selected_file_name()
            if not file_name:
                QMessageBox.information(
                    self, "Нет файла",
                    "Сначала выберите находку или файл в списке слева."
                )
                return
            pos = 0
            length = 0

        content = next(
            (lf.content for lf in self.app.files if lf.name == file_name),
            None,
        )
        if content is None:
            QMessageBox.warning(self, "Не найдено",
                                "Файл не найден среди загруженных.")
            return

        self._show_viewer(file_name, content, pos, length)

    def _show_viewer(self, file_name: str, content: str, pos: int, length: int):
        if file_name in self._viewer_windows:
            win = self._viewer_windows[file_name]
            if win.isMinimized():
                win.showNormal()
            win.raise_()
            win.activateWindow()
            if pos > 0:
                win._jump(pos, length)
            return

        # Убрали self из аргументов!
        win = FileViewerWindow(
            file_name, content, pos, length,
            on_create_rule=self._create_rule_from_text,
        )
        win.setAttribute(Qt.WA_DeleteOnClose)
        win.destroyed.connect(lambda: self._viewer_windows.pop(file_name, None))
        
        self._viewer_windows[file_name] = win
        win.show()

    def _create_rule_from_text(self, text: str):
        dlg = RuleFromSelectionDialog(self, text)
        if dlg.exec() != QDialog.Accepted or not dlg.result_rule:
            return
        self.app.rules.append(dlg.result_rule)
        save_rules(self.app.rules)
        self.app.rules_tab.refresh()
        self.run_analysis()
        QMessageBox.information(
            self, "Правило создано",
            f"Правило «{dlg.result_rule.name}» добавлено. "
            f"Отредактировать можно во вкладке «Правила»."
        )

    # ───────── Действия с находкой ─────────
    def mark_false_positive(self):
        f = self.current
        if not f:
            return
        if f.ignore_note:
            QMessageBox.information(
                self, "Уже есть",
                "Этот случай уже помечен как ложное срабатывание."
            )
            return
        self.app.notes.append(Note(
            id="note-" + uuid.uuid4().hex[:10],
            rule_id=f.rule_id, signature=f.signature, kind="ignore",
            title=f"Ложное срабатывание: {f.rule_name}",
            preview=f.context[:400],
            created_at=datetime.utcnow().isoformat() + "Z",
        ))
        save_notes(self.app.notes)
        self.run_analysis()
        self.app.refresh_note_tabs()

    def add_note(self):
        f = self.current
        if not f:
            return
        dlg = NoteDialog(self, finding=f)
        if dlg.exec() != QDialog.Accepted or not dlg.result_note:
            return
        self.app.notes.append(dlg.result_note)
        save_notes(self.app.notes)
        self.run_analysis()
        self.app.refresh_note_tabs()

    def edit_rule(self):
        f = self.current
        if not f:
            return
        self.app.tabs.setCurrentWidget(self.app.rules_tab)
        self.app.rules_tab.select_rule(f.rule_id)

    # ───────── Восстановление скрытых ─────────
    def restore_hidden_selected(self):
        rows = sorted({ix.row() for ix in self.hidden_table.selectedIndexes()})
        if not rows:
            return
        ids = []
        for r in rows:
            it = self.hidden_table.item(r, COL_ICON)
            if not it:
                continue
            f = next((x for x in self.app.findings
                      if id(x) == it.data(Qt.UserRole)), None)
            if f:
                n = f.ignore_note
                if n:
                    ids.append(n.id)
        if not ids:
            return
        id_set = set(ids)
        self.app.notes = [n for n in self.app.notes if n.id not in id_set]
        save_notes(self.app.notes)
        self.run_analysis()
        self.app.refresh_note_tabs()

    def restore_all_hidden(self):
        ids = [n.id for n in self.app.notes if n.kind == "ignore"]
        if not ids:
            return
        if QMessageBox.question(
            self, "Вернуть все",
            f"Снять {len(ids)} исключений?\n"
            "Все эти находки снова будут показаны."
        ) != QMessageBox.Yes:
            return
        self.app.notes = [n for n in self.app.notes if n.kind != "ignore"]
        save_notes(self.app.notes)
        self.run_analysis()
        self.app.refresh_note_tabs()