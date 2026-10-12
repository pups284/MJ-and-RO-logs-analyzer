from __future__ import annotations

from PySide6.QtCore import QEvent, QTimer
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QStatusBar,
    QTabWidget, QVBoxLayout, QWidget,
)

from ..models import LoadedFile
from ..platform_win import apply_dark_title_bar
from ..storage import load_notes, load_rules
from .analyze_tab import AnalyzeTab
from .notes_tab import NotesTab
from .rules_tab import RulesTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Majestic Log Analyzer")
        self.resize(1500, 950)
        self.setMinimumSize(1100, 720)

        self.rules = load_rules()
        self.notes = load_notes()
        self.files: list[LoadedFile] = []
        self.findings = []

        # ── Drag & Drop ──
        self.setAcceptDrops(True)
        self._drag_active = False
        self._drag_timer = QTimer(self)
        self._drag_timer.setSingleShot(True)
        self._drag_timer.setInterval(200)
        self._drag_timer.timeout.connect(lambda: self._set_drag_active(False))
        QApplication.instance().installEventFilter(self)

        central = QWidget()
        central.setObjectName("CentralRoot")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 14, 16, 8)
        root.setSpacing(12)

        header = QFrame(); header.setObjectName("HeaderBar"); header.setFixedHeight(62)
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(18, 8, 18, 8); hlay.setSpacing(14)

        tb = QVBoxLayout(); tb.setContentsMargins(0, 0, 0, 0); tb.setSpacing(0)
        t = QLabel("Majestic Log Analyzer"); t.setObjectName("AppTitle")
        s = QLabel("Локальный анализ логов игрового лаунчера"); s.setObjectName("AppSubtitle")
        tb.addWidget(t); tb.addWidget(s)
        hlay.addLayout(tb); hlay.addStretch(1)

        self.badge_rules = QLabel(); self.badge_rules.setObjectName("AppBadge")
        self.badge_notes = QLabel(); self.badge_notes.setObjectName("AppBadge")
        self.badge_files = QLabel(); self.badge_files.setObjectName("AppBadge")
        self.badge_finds = QLabel(); self.badge_finds.setObjectName("AppBadge")
        for b in (self.badge_rules, self.badge_notes, self.badge_files, self.badge_finds):
            hlay.addWidget(b)
        root.addWidget(header)

        self.tabs = QTabWidget(); root.addWidget(self.tabs, 1)

        self.analyze_tab = AnalyzeTab(self)
        self.rules_tab   = RulesTab(self)
        self.notes_tab   = NotesTab(self)

        self.tabs.addTab(self.analyze_tab, "Анализ")
        self.tabs.addTab(self.rules_tab,   "Правила")
        self.tabs.addTab(self.notes_tab,   "Исключения и примечания")

        self.setStatusBar(QStatusBar())
        self.update_status()

    # ───────── Drag & Drop ─────────
    def eventFilter(self, obj, event):
        et = event.type()
        if et in (QEvent.DragEnter, QEvent.DragMove, QEvent.Drop):
            if (isinstance(obj, QWidget)
                    and obj.window() is self
                    and event.mimeData().hasUrls()):
                if et == QEvent.DragEnter:
                    event.acceptProposedAction()
                    self._set_drag_active(True)
                elif et == QEvent.DragMove:
                    event.acceptProposedAction()
                    self._drag_timer.start()
                else:
                    self._drag_timer.stop()
                    self._set_drag_active(False)
                    self._handle_drop(event)
                return True
        return super().eventFilter(obj, event)

    def _handle_drop(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if not paths:
            event.ignore()
            return
        event.acceptProposedAction()
        self.tabs.setCurrentWidget(self.analyze_tab)
        self.analyze_tab.add_files(paths)

    def _set_drag_active(self, active: bool):
        if self._drag_active == active:
            return
        self._drag_active = active
        cw = self.centralWidget()
        cw.setProperty("dragging", "true" if active else "false")
        cw.style().unpolish(cw)
        cw.style().polish(cw)
        cw.update()

    def update_status(self):
        n_rules = len(self.rules)
        n_enabled = sum(1 for r in self.rules if r.enabled)
        n_notes = len(self.notes)
        n_files = len(self.files)
        n_visible = sum(1 for f in self.findings if not f.is_hidden)
        n_hidden = sum(1 for f in self.findings if f.is_hidden)

        self.badge_rules.setText(f"Правила: {n_enabled}/{n_rules}")
        self.badge_notes.setText(f"Примечания: {n_notes}")
        self.badge_files.setText(f"Файлы: {n_files}")
        self.badge_finds.setText(f"Находки: {n_visible}")

        self.statusBar().showMessage(
            f"Правила: {n_enabled}/{n_rules}    ·    "
            f"Примечания: {n_notes}    ·    Файлов: {n_files}    ·    "
            f"Находок: {n_visible}    ·    Скрыто: {n_hidden}    ·    "
            f"💡 Перетащите .log в любое место окна"
        )

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self)

    def closeEvent(self, event):
        try:
            removed = self.analyze_tab.cleanup_discord_files()
            if removed:
                print(f"[cleanup] removed {removed} discord temp file(s)")
        except Exception as e:
            print("cleanup failed:", e)
        super().closeEvent(event)