from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, QPoint, QRect, QSize
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QStatusBar, QTabWidget, QVBoxLayout, QWidget,
)

from ..models import LoadedFile
from ..platform_win import apply_dark_title_bar
from ..storage import load_notes, load_rules, load_ui, save_ui
from ..style import DARK_STYLE, LIGHT_STYLE, SPACE, theme_tokens
from .analyze_tab import AnalyzeTab
from .common import BrandMark, fade_in, make_icon, make_state_icon
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
        app = QApplication.instance()
        theme = app.property("theme") if app else "dark"
        tokens = theme_tokens(theme or "dark")
        dim_color = QColor(0, 0, 0, 160)

        if not self.rect_to_highlight:
            painter.fillRect(self.rect(), dim_color)
            return

        r = self.rect_to_highlight
        w, h = self.width(), self.height()

        painter.fillRect(0, 0, w, r.top(), dim_color)
        painter.fillRect(0, r.bottom(), w, h - r.bottom(), dim_color)
        painter.fillRect(0, r.top(), r.left(), r.height(), dim_color)
        painter.fillRect(r.right(), r.top(), w - r.right(), r.height(), dim_color)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(tokens["accent"]), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(r, 8, 8)


class MainWindow(QMainWindow):
    PAGE_META = (
        ("Анализ логов", "Загрузите логи, чтобы найти проблемы и подготовить ответ игроку."),
        ("Правила", "Условия, по которым анализатор ищет ошибки в логах."),
        ("Примечания", "Заметки к найденным ошибкам и их сигнатурам."),
        ("Исключения", "Ложные срабатывания, скрытые из основной таблицы."),
    )

    NAV_SPECS = (
        ("analysis", "Анализ", 0),
        ("rules", "Правила", 1),
        ("notes", "Примечания", 2),
        ("exceptions", "Исключения", 3),
    )

    def __init__(self):
        super().__init__()
        app = QApplication.instance()
        if app and not app.windowIcon().isNull():
            self.setWindowIcon(app.windowIcon())
        self.setWindowTitle("Majestic Log Analyzer")
        self.resize(1500, 950)
        self.setMinimumSize(1080, 700)

        self._compact = None
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
        central.setObjectName("AppShell")
        self.setCentralWidget(central)
        shell = QHBoxLayout(central)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        self.analyze_tab = AnalyzeTab(self)
        self.rules_tab = RulesTab(self)
        self.notes_tab = NotesTab(self)
        self.exceptions_tab = ExceptionsTab(self)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("MainTabs")
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().hide()
        self.tabs.addTab(self.analyze_tab, "Анализ")
        self.tabs.addTab(self.rules_tab, "Правила")
        self.tabs.addTab(self.notes_tab, "Примечания")
        self.tabs.addTab(self.exceptions_tab, "Исключения")

        shell.addWidget(self._build_sidebar())
        shell.addWidget(self._build_content(), 1)

        self.setStatusBar(QStatusBar())
        self.update_status()

        self._apply_theme()
        self._sync_page(0)
        self._set_sidebar_compact(self.width() < 1240)

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
            {"tab": 0, "widget": None, "title": "Готово!", "text": "Вы всегда можете открыть это обучение заново, нажав на кнопку «?» в правом нижнем углу."},
        ]

        if not self.ui_settings.get("tutorial_shown", False):
            QTimer.singleShot(800, self._start_tutorial)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(236)
        self.sidebar = sidebar

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(SPACE["md"])
        self.sidebar_layout = layout

        self.brand_row = QHBoxLayout()
        self.brand_row.setContentsMargins(0, 0, 0, 0)
        self.brand_row.setSpacing(10)
        self.brand_mark = BrandMark(38)
        self.brand_row.addWidget(self.brand_mark, 0, Qt.AlignLeft)

        self.brand_text = QWidget()
        brand_text_layout = QVBoxLayout(self.brand_text)
        brand_text_layout.setContentsMargins(0, 0, 0, 0)
        brand_text_layout.setSpacing(1)
        brand_name = QLabel("Majestic")
        brand_name.setObjectName("BrandName")
        brand_kind = QLabel("LOG ANALYZER")
        brand_kind.setObjectName("BrandKind")
        brand_text_layout.addWidget(brand_name)
        brand_text_layout.addWidget(brand_kind)
        self.brand_row.addWidget(self.brand_text, 1)
        layout.addLayout(self.brand_row)

        rule = QFrame()
        rule.setObjectName("SidebarRule")
        layout.addWidget(rule)
        layout.addSpacing(SPACE["xs"])

        nav_caption = QLabel("РАЗДЕЛЫ")
        nav_caption.setObjectName("SidebarSection")
        layout.addWidget(nav_caption)
        self.sidebar_sections = [nav_caption]

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_specs = []

        for icon_name, text, index in self.NAV_SPECS:
            button = QPushButton(text)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(38)
            button.setIconSize(QSize(18, 18))
            button.setIcon(make_state_icon(icon_name, "#9297A1", "#C71A4E", 18))
            button.clicked.connect(
                lambda _checked=False, i=index: self.tabs.setCurrentIndex(i)
            )
            self.nav_group.addButton(button, index)
            layout.addWidget(button)
            self.nav_specs.append(
                {
                    "icon": icon_name,
                    "text": text,
                    "index": index,
                    "button": button,
                }
            )

        layout.addStretch(1)

        self.status_card = QFrame()
        self.status_card.setObjectName("SidebarCard")
        status_layout = QHBoxLayout(self.status_card)
        status_layout.setContentsMargins(10, 8, 10, 8)
        status_layout.setSpacing(8)
        self.status_layout = status_layout

        self.status_dot = QLabel("●")
        self.status_dot.setObjectName("SidebarDot")
        status_layout.addWidget(self.status_dot, 0, Qt.AlignTop)

        self.status_text = QWidget()
        status_text_layout = QVBoxLayout(self.status_text)
        status_text_layout.setContentsMargins(0, 0, 0, 0)
        status_text_layout.setSpacing(1)
        status_title = QLabel("Локальный режим")
        status_title.setObjectName("SidebarStatusTitle")
        status_note = QLabel("Данные остаются на устройстве")
        status_note.setObjectName("SidebarStatusText")
        status_note.setWordWrap(True)
        status_text_layout.addWidget(status_title)
        status_text_layout.addWidget(status_note)
        status_layout.addWidget(self.status_text, 1)
        layout.addWidget(self.status_card)

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.setSpacing(8)
        self.btn_theme = QPushButton()
        self.btn_theme.setObjectName("IconButton")
        self.btn_theme.setCursor(Qt.PointingHandCursor)
        self.btn_theme.setToolTip("Переключить тему")
        self.btn_theme.clicked.connect(self._toggle_theme)
        self.btn_help = QPushButton()
        self.btn_help.setObjectName("IconButton")
        self.btn_help.setCursor(Qt.PointingHandCursor)
        self.btn_help.setToolTip("Обучение")
        self.btn_help.clicked.connect(self._start_tutorial)
        footer.addWidget(self.btn_theme)
        footer.addWidget(self.btn_help)
        footer.addStretch(1)
        layout.addLayout(footer)

        return sidebar

    def _stat_chip(self, caption: str) -> tuple[QFrame, QLabel]:
        chip = QFrame()
        chip.setObjectName("StatChip")
        chip.setFixedHeight(46)
        chip.setMinimumWidth(88)
        layout = QVBoxLayout(chip)
        layout.setContentsMargins(11, 5, 11, 5)
        layout.setSpacing(0)
        label = QLabel(caption.upper())
        label.setObjectName("StatCaption")
        value = QLabel("0")
        value.setObjectName("StatValue")
        layout.addWidget(label)
        layout.addWidget(value)
        return chip, value

    def _build_content(self) -> QWidget:
        content = QWidget()
        content.setObjectName("ContentArea")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(
            SPACE["xl"], SPACE["lg"] + 4, SPACE["xl"], SPACE["md"]
        )
        layout.setSpacing(SPACE["lg"])

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(SPACE["xl"])

        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(2)
        self.page_title = QLabel()
        self.page_title.setObjectName("PageTitle")
        self.page_subtitle = QLabel()
        self.page_subtitle.setObjectName("PageSubtitle")
        title_box.addWidget(self.page_title)
        title_box.addWidget(self.page_subtitle)
        header_layout.addLayout(title_box, 1)

        self.stats_box = QWidget()
        stats_layout = QHBoxLayout(self.stats_box)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(SPACE["sm"])

        rules_chip, self.badge_rules = self._stat_chip("Правила")
        notes_chip, self.badge_notes = self._stat_chip("Примечания")
        files_chip, self.badge_files = self._stat_chip("Файлы")
        finds_chip, self.badge_finds = self._stat_chip("Находки")
        for chip in (rules_chip, notes_chip, files_chip, finds_chip):
            stats_layout.addWidget(chip)
        header_layout.addWidget(self.stats_box, 0, Qt.AlignTop)

        layout.addWidget(header)
        layout.addWidget(self.tabs, 1)

        self.tabs.currentChanged.connect(self._sync_page)
        return content

    def _sync_page(self, index: int) -> None:
        if not 0 <= index < len(self.PAGE_META):
            return
        title, subtitle = self.PAGE_META[index]
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)
        for spec in getattr(self, "nav_specs", []):
            spec["button"].setChecked(spec["index"] == index)
        widget = self.tabs.widget(index)

    def _set_sidebar_compact(self, compact: bool) -> None:
        if self._compact == compact:
            return
        self._compact = compact
        self.sidebar.setFixedWidth(96 if compact else 236)
        if compact:
            self.sidebar_layout.setContentsMargins(12, 16, 12, 14)
        else:
            self.sidebar_layout.setContentsMargins(16, 20, 16, 16)

        self.brand_text.setVisible(not compact)
        for label in self.sidebar_sections:
            label.setVisible(not compact)
        self.status_text.setVisible(not compact)
        self.brand_row.setAlignment(
            self.brand_mark, Qt.AlignHCenter if compact else Qt.AlignLeft
        )
        self.status_layout.setAlignment(
            self.status_dot, Qt.AlignHCenter if compact else Qt.AlignTop
        )

        for spec in self.nav_specs:
            button = spec["button"]
            button.setText("" if compact else spec["text"])
            button.setToolTip(spec["text"] if compact else "")
            button.setProperty("compact", "true" if compact else "false")
            button.style().unpolish(button)
            button.style().polish(button)

    def _refresh_icons(self) -> None:
        tokens = theme_tokens(self.current_theme)
        for spec in self.nav_specs:
            spec["button"].setIcon(
                make_state_icon(
                    spec["icon"], tokens["muted"], tokens["accent"], 18
                )
            )
        theme_icon = "sun" if self.current_theme == "dark" else "moon"
        self.btn_theme.setIcon(make_icon(theme_icon, tokens["muted"], 17))
        self.btn_help.setIcon(make_icon("help", tokens["muted"], 17))
        self.brand_mark.update()

    def _toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        QApplication.instance().setProperty("theme", self.current_theme)
        self.ui_settings["theme"] = self.current_theme
        save_ui(self.ui_settings)
        self._apply_theme()

    def _apply_theme(self):
        style = LIGHT_STYLE if self.current_theme == "light" else DARK_STYLE
        QApplication.instance().setStyleSheet(style)
        self._refresh_icons()
        apply_dark_title_bar(self)
        if hasattr(self, "analyze_tab"):
            self.analyze_tab.apply_theme_colors()
        if hasattr(self, "exceptions_tab"):
            self.exceptions_tab.apply_theme_colors()
        if hasattr(self, "overlay") and self.overlay:
            self.overlay.update()

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

                if py + self.popup.height() > screen.bottom():
                    py = global_pos.y() - self.popup.height() - 15
                if py < screen.top():
                    py = screen.top() + 15
                if px + self.popup.width() > screen.right():
                    px = screen.right() - self.popup.width() - 15

                self.popup.move(px, py)
        else:
            self.overlay.set_highlight(None)
            c_rect = self.geometry()
            self.popup.move(
                c_rect.center().x() - self.popup.width() // 2,
                c_rect.center().y() - self.popup.height() // 2,
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
        if getattr(self, "sidebar", None) is not None:
            self._set_sidebar_compact(self.width() < 1240)
        if getattr(self, "stats_box", None) is not None:
            self.stats_box.setVisible(self.width() >= 1120)
        if hasattr(self, "overlay") and self.overlay:
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

        self.badge_rules.setText(f"{n_enabled}/{n_rules}")
        self.badge_notes.setText(str(n_notes))
        self.badge_files.setText(str(n_files))
        self.badge_finds.setText(str(n_visible))

        if n_files:
            message = (
                f"Файлов: {n_files}    ·    Находок: {n_visible}    ·    "
                f"Скрыто: {n_hidden}    ·    Исключений: {n_exc}"
            )
        else:
            message = "Перетащите .log в любое место окна или нажмите «Загрузить логи…»"
        self.statusBar().showMessage(message)

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self)
        if not getattr(self, "_shown_once", False):
            self._shown_once = True
            QTimer.singleShot(
                0,
                lambda: fade_in(self.tabs.widget(self.tabs.currentIndex()), 220),
            )

    def closeEvent(self, event):
        self.analyze_tab.close_all_viewers()
        super().closeEvent(event)
