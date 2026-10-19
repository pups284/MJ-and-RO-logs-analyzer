from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, QPoint, QRect
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QStatusBar, QTabWidget, QVBoxLayout, QWidget
)

from ..models import LoadedFile
from ..platform_win import apply_dark_title_bar
from ..storage import load_notes, load_rules, load_ui, save_ui
from ..style import DARK_STYLE, LIGHT_STYLE
from .analyze_tab import AnalyzeTab
from .exceptions_tab import ExceptionsTab
from .notes_tab import NotesTab
from .rules_tab import RulesTab
from .tutorial_dialog import TutorialPopup


class TutorialOverlay(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.rect_to_highlight = None
        self.hide()

    def set_highlight(self, widget):
        if not widget or not widget.isVisible():
            self.rect_to_highlight = None
            self.hide()
            return

        p = widget.mapTo(self.parentWidget(), QPoint(0, 0))
        self.rect_to_highlight = QRect(p, widget.size()).adjusted(-6, -6, 6, 6)
        
        self.resize(self.parentWidget().size())
        self.show()
        self.raise_()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        dim_color = QColor(0, 0, 0, 170)

        if not self.rect_to_highlight:
            painter.fillRect(self.rect(), dim_color)
            return

        r = self.rect_to_highlight
        w, h = self.width(), self.height()

        # Затемняем 4 стороны вокруг выделения, оставляя "дырку"
        painter.fillRect(0, 0, w, r.top(), dim_color)  # Top
        painter.fillRect(0, r.bottom(), w, h - r.bottom(), dim_color)  # Bottom
        painter.fillRect(0, r.top(), r.left(), r.height(), dim_color)  # Left
        painter.fillRect(r.right(), r.top(), w - r.right(), r.height(), dim_color)  # Right

        # Синяя рамка
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#6d5cff"), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(r, 6, 6)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        app = QApplication.instance()
        if app and not app.windowIcon().isNull():
            self.setWindowIcon(app.windowIcon())
        self.setWindowTitle("Majestic Log Analyzer")
        self.resize(1500, 950)
        self.setMinimumSize(1100, 720)

        self.ui_settings = load_ui()
        self.current_theme = self.ui_settings.get("theme", "dark")
        app.setProperty("theme", self.current_theme)

        self.rules = load_rules()
        self.notes = load_notes()
        self.files: list[LoadedFile] = []
        self.findings = []

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

        header = QFrame()
        header.setObjectName("HeaderBar")
        header.setFixedHeight(62)
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(18, 8, 18, 8)
        hlay.setSpacing(14)

        tb = QVBoxLayout()
        tb.setContentsMargins(0, 0, 0, 0)
        tb.setSpacing(0)
        t = QLabel("Majestic Log Analyzer"); t.setObjectName("AppTitle")
        s = QLabel("Локальный анализ логов игрового лаунчера")
        s.setObjectName("AppSubtitle")
        tb.addWidget(t)
        tb.addWidget(s)
        hlay.addLayout(tb)
        hlay.addStretch(1)

        self.badge_rules = QLabel(); self.badge_rules.setObjectName("AppBadge")
        self.badge_notes = QLabel(); self.badge_notes.setObjectName("AppBadge")
        self.badge_files = QLabel(); self.badge_files.setObjectName("AppBadge")
        self.badge_finds = QLabel(); self.badge_finds.setObjectName("AppBadge")
        for b in (self.badge_rules, self.badge_notes, self.badge_files, self.badge_finds):
            hlay.addWidget(b)

        btn_theme = QPushButton("🌙 / ☀️")
        btn_theme.setObjectName("Ghost")
        btn_theme.setToolTip("Переключить тему")
        btn_theme.setFixedWidth(60)
        btn_theme.clicked.connect(self._toggle_theme)
        hlay.addWidget(btn_theme)

        btn_help = QPushButton("?")
        btn_help.setObjectName("Ghost")
        btn_help.setToolTip("Обучение")
        btn_help.setFixedWidth(34)
        btn_help.clicked.connect(self._start_tutorial)
        hlay.addWidget(btn_help)

        root.addWidget(header)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        self.analyze_tab = AnalyzeTab(self)
        self.rules_tab = RulesTab(self)
        self.notes_tab = NotesTab(self)
        self.exceptions_tab = ExceptionsTab(self)

        self.tabs.addTab(self.analyze_tab, "Анализ")
        self.tabs.addTab(self.rules_tab, "Правила")
        self.tabs.addTab(self.notes_tab, "Примечания")
        self.tabs.addTab(self.exceptions_tab, "Исключения")

        self.setStatusBar(QStatusBar())
        self.update_status()

        self._apply_theme()

        self.overlay = TutorialOverlay(central)
        self.popup = TutorialPopup(self)
        self.popup.next_clicked.connect(self._next_tutorial_step)
        self.popup.prev_clicked.connect(self._prev_tutorial_step)
        self.popup.skip_clicked.connect(self._end_tutorial)
        self.tutorial_step = 0

        self.steps = [
            {"tab": 0, "widget": None, "title": "Добро пожаловать!", "text": "Majestic Log Analyzer — быстрый офлайн-анализ логов.\nДавайте посмотрим, где что находится."},
            {"tab": 0, "widget": self.analyze_tab.btn_load, "title": "Загрузка логов", "text": "Нажмите сюда, чтобы выбрать файлы, или просто перетащите .log в любое место окна."},
            {"tab": 0, "widget": self.analyze_tab.table, "title": "Находки", "text": "Здесь появляются найденные проблемы. Нажмите на любую строку, чтобы увидеть детали."},
            {"tab": 0, "widget": self.analyze_tab.detail_title, "title": "Детали", "text": "В этой панели вы найдёте объяснение проблемы и готовый ответ для игрока."},
            {"tab": 1, "widget": self.rules_tab.list, "title": "Вкладка «Правила»", "text": "Здесь хранятся правила, по которым программа ищет ошибки в логах."},
            {"tab": 1, "widget": self.rules_tab.f_all, "title": "Условия правила", "text": "Например, «Должны встречаться» — это список слов, которые обязаны быть в логе, чтобы сработало правило."},
            {"tab": 1, "widget": self.rules_tab.b_save, "title": "Сохранение и синхронизация", "text": "После изменения правил их нужно сохранить или обновить из GitHub."},
            {"tab": 2, "widget": self.notes_tab.list, "title": "Вкладка «Примечания»", "text": "Оставляйте заметки к найденным ошибкам, чтобы не забыть важные детали."},
            {"tab": 3, "widget": self.exceptions_tab.table, "title": "Вкладка «Исключения»", "text": "Сюда попадают ложные срабатывания, которые нужно скрыть из основной таблицы."},
            {"tab": 0, "widget": None, "title": "Готово!", "text": "Вы всегда можете открыть это обучение заново, нажав на кнопку «?» в правом верхнем углу."}
        ]

        if not self.ui_settings.get("tutorial_shown", False):
            QTimer.singleShot(800, self._start_tutorial)

    def _toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        QApplication.instance().setProperty("theme", self.current_theme)
        self.ui_settings["theme"] = self.current_theme
        save_ui(self.ui_settings)
        self._apply_theme()

    def _apply_theme(self):
        style = LIGHT_STYLE if self.current_theme == "light" else DARK_STYLE
        QApplication.instance().setStyleSheet(style)
        apply_dark_title_bar(self)

    def _start_tutorial(self):
        self.ui_settings["tutorial_shown"] = True
        save_ui(self.ui_settings)
        self.tutorial_step = 0
        self.popup.show()
        self._next_tutorial_step()

    def _end_tutorial(self):
        self.popup.hide()
        self.overlay.hide()
        self.tutorial_step = 0

    def _position_popup(self):
        if not self.popup.isVisible() or self.tutorial_step == 0:
            return
            
        step = self.steps[self.tutorial_step - 1]
        w = step["widget"]
        
        if w:
            self.overlay.set_highlight(w)
            rect = self.overlay.rect_to_highlight
            if rect:
                global_pos = self.overlay.mapToGlobal(rect.topLeft())
                px = global_pos.x() + 15
                py = global_pos.y() + rect.height() + 15

                screen = QApplication.primaryScreen().availableGeometry()
                
                # Если не влезает снизу — ставим сверху
                if py + self.popup.height() > screen.bottom():
                    py = global_pos.y() - self.popup.height() - 15
                # Если не влезает сверху — прижимаем к верху экрана
                if py < screen.top():
                    py = screen.top() + 15
                # Если не влезает справа — прижимаем к правому краю
                if px + self.popup.width() > screen.right():
                    px = screen.right() - self.popup.width() - 15

                self.popup.move(px, py)
        else:
            self.overlay.set_highlight(None)
            c_rect = self.geometry()
            self.popup.move(
                c_rect.center().x() - self.popup.width() // 2,
                c_rect.center().y() - self.popup.height() // 2
            )

    def _next_tutorial_step(self):
        if self.tutorial_step >= len(self.steps):
            self._end_tutorial()
            return

        step = self.steps[self.tutorial_step]
        if step["tab"] is not None:
            self.tabs.setCurrentIndex(step["tab"])

        self.popup.set_step(step["title"], step["text"], self.tutorial_step + 1, len(self.steps))
        self.popup.show()
        self.popup.raise_()
        
        self.tutorial_step += 1
        self._position_popup()

    def _prev_tutorial_step(self):
        if self.tutorial_step > 1:
            self.tutorial_step -= 2
            self._next_tutorial_step()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'overlay') and self.overlay:
            self.overlay.resize(self.centralWidget().size())
            self._position_popup()

    def refresh_note_tabs(self):
        self.notes_tab.refresh()
        self.exceptions_tab.refresh()

    def eventFilter(self, obj, event):
        et = event.type()
        if et in (event.Type.DragEnter, event.Type.DragMove, event.Type.Drop):
            if (isinstance(obj, QWidget) and obj.window() is self and event.mimeData().hasUrls()):
                if et == event.Type.DragEnter:
                    event.acceptProposedAction()
                    self._set_drag_active(True)
                elif et == event.Type.DragMove:
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
        n_notes = sum(1 for n in self.notes if n.kind == "note")
        n_exc = sum(1 for n in self.notes if n.kind == "ignore")
        n_files = len(self.files)
        n_visible = sum(1 for f in self.findings if not f.is_hidden)
        n_hidden = sum(1 for f in self.findings if f.is_hidden)

        self.badge_rules.setText(f"Правила: {n_enabled}/{n_rules}")
        self.badge_notes.setText(f"Примечания: {n_notes}")
        self.badge_files.setText(f"Файлы: {n_files}")
        self.badge_finds.setText(f"Находки: {n_visible}")

        self.statusBar().showMessage(
            f"Правила: {n_enabled}/{n_rules}    ·    "
            f"Примечания: {n_notes}    ·    Исключения: {n_exc}    ·    "
            f"Файлов: {n_files}    ·    Находок: {n_visible}    ·    Скрыто: {n_hidden}    ·    "
            f"💡 Перетащите .log в любое место окна"
        )

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self)

    def closeEvent(self, event):
        # Закрываем все открытые окна редактора
        for win in list(self.analyze_tab._viewer_windows.values()):
            win.close()
            
        super().closeEvent(event)