from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import QRect, QSize, Qt, QTimer, QRegularExpression
from PySide6.QtGui import (
    QColor, QFont, QFontDatabase, QKeySequence, QPainter, QPen,
    QShortcut, QSyntaxHighlighter, QTextCharFormat, QTextCursor,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPlainTextEdit, QPushButton, QTextEdit, QVBoxLayout, QWidget,
)

from ..platform_win import apply_dark_title_bar
from .common import section_label


_MONO_CANDIDATES = (
    "Cascadia Mono", "Cascadia Code", "JetBrains Mono",
    "Consolas", "Courier New", "Menlo", "Monaco", "DejaVu Sans Mono",
)


def _pick_mono_font() -> QFont:
    families = set(QFontDatabase.families())
    font = QFont()
    for name in _MONO_CANDIDATES:
        if name in families:
            font.setFamily(name)
            break
    else:
        font.setStyleHint(QFont.Monospace)
        font.setFamily("monospace")
    font.setStyleHint(QFont.Monospace)
    font.setFixedPitch(True)
    font.setPointSizeF(10.0)
    return font


# ═══════════════════════════ Подсветка ═══════════════════════════

class MajesticLogHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument):
        super().__init__(document)
        
        # Заранее создаём форматы (чтобы не делать это на каждой строке)
        self.fmt_ts     = self._fmt("#6b7385")
        self.fmt_ok     = self._fmt("#7ee787", bold=True)
        self.fmt_warn   = self._fmt("#ffb547")
        self.fmt_err    = self._fmt("#ff5470", bold=True)
        self.fmt_tag    = self._fmt("#a99bff")
        self.fmt_ok_txt = self._fmt("#7ee787")
        self.fmt_err_txt= self._fmt("#ff5470")
        self.fmt_neutral= self._fmt("#8b94a3")
        self.fmt_server = self._fmt("#4dd0e1")
        self.fmt_info   = self._fmt("#4dd0e1")

        # Скомпилированные регулярные выражения (объединяем по цветам)
        self.re_ts = QRegularExpression(r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\]|\[\d{2}:\d{2}:\d{2}(?:\.\d{3})?\]")
        
        self.re_warn = QRegularExpression(
            r"\[(?:warn|warning|debug|trace)\]"
            r"|\bERR_[A-Z0-9_]+\b"
            r"|'(?:TIMEOUT|NETWORK|ABORTED)'"
        )

        self.re_err = QRegularExpression(
            r"\[(?:Error|ERROR|Warning|WARNING)\]"
            r"|\b(?:error|Error|ERROR|fatal|Fatal|FATAL|critical|Critical|CRITICAL|crashed|failed|exception)\b"
        )

        self.re_tag = QRegularExpression(
            r"\[\s*\([\w.\-]+\)\s*\]"
            r"|\[(?:MAJESTIC|LAUNCH|GAME|BACKUP|CRASH|DOWNLOADER|REVALIDATE|HASHMAP|REQUEST|HOSTING|AUTH|DOWNLOAD|DISKS|DISPLAY|EMAIL|EPIC|FSR|INIT|MACRO|MASTERLIST|MIGRATE|MODSLIST|PERMISSIONS|QUEUE|RGL|SECURE|SIGN_IN|SIGN_UP|STEAM|TRUSTED_DEVICES|UPDATER|WEB|CHECKFILE|CLOTHES|DC|AUTH_HISTORY|MODSCATEGORIESLIST|NEW_PASSWORD|hooks|web|net|voice|res|sync|discord|gui|js|assets|render|hooks\.pool|hooks\.ped|res\.download|js\.script)\]"
            r"|\bMAJESTIC:"
        )

        self.re_ok = QRegularExpression(
            r"\bsuccess:\s*true\b"
            r"|\b(?:ok|success|initialized|loaded|completed)\b"
            r"|\btrue\b"
        )

        self.re_info = QRegularExpression(r"\[info\]")
        self.re_neutral = QRegularExpression(r"\b(?:false|null|undefined)\b")
        self.re_server = QRegularExpression(r"\b(?:ru\d{1,2}|eu\d|us\d|boston|detroit|chicago|dallas|san-diego|atlanta|las-vegas|los-angeles|san-francisco|washington|miami|tverskoy|memphis)\b")

    @staticmethod
    def _fmt(color: str, *, bold: bool = False) -> QTextCharFormat:
        f = QTextCharFormat()
        f.setForeground(QColor(color))
        if bold:
            f.setFontWeight(QFont.Bold)
        return f

    def highlightBlock(self, text: str) -> None:
        if not text:
            return

        # Быстрая проверка подстрок (в C++ это работает моментально)
        low = text.lower()

        # 1. Таймстемп
        if "[" in text:
            it = self.re_ts.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), self.fmt_ts)

        # 2. Info
        if "[info]" in low:
            it = self.re_info.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), self.fmt_info)

        # 3. Warn / ERR_
        if "warn" in low or "debug" in low or "trace" in low or "err_" in low or "timeout" in low or "network" in low or "aborted" in low:
            it = self.re_warn.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), self.fmt_warn)

        # 4. Error
        if "error" in low or "fatal" in low or "critical" in low or "crashed" in low or "failed" in low or "exception" in low or "[warning]" in low:
            it = self.re_err.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), self.fmt_err)

        # 5. Теги модулей
        if "(" in text or "majestic" in low:
            it = self.re_tag.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), self.fmt_tag)

        # 6. Позитивные маркеры
        if "true" in low or "ok" in low or "success" in low or "loaded" in low or "initialized" in low:
            it = self.re_ok.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), self.fmt_ok_txt)

        # 7. Нейтральные (false, null)
        if "false" in low or "null" in low or "undefined" in low:
            it = self.re_neutral.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), self.fmt_neutral)

        # 8. Сервера
        if "ru" in low or "miami" in low or "tverskoy" in low:
            it = self.re_server.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), self.fmt_server)


# ═══════════════════════════ Миникарта (Текстовая) ═══════════════════════════

_MM_TEXT_DEFAULT = "#3d4355"
_MM_TEXT_DEBUG   = "#2e3444"
_MM_TEXT_WARN    = "#a07a2a"
_MM_TEXT_ERROR   = "#b04050"
_MM_TEXT_OK      = "#3d8a52"
_MM_TEXT_TAG     = "#6a5da8"


def _minimap_line_color(text: str) -> str:
    if not text: return _MM_TEXT_DEBUG
    low = text.lower()

    if ("err_" in low or "[error]" in low or "\"error\"" in low or "'error'" in low
            or " fatal" in low or " crashed" in low or "failed:" in low or " failed" in low):
        return _MM_TEXT_ERROR
    if "[warn" in low: return _MM_TEXT_WARN
    if "success" in low or "loaded" in low or " ok " in f" {low} ": return _MM_TEXT_OK
    if "majestic:" in low or "(patcher)" in low or "(client)" in low: return _MM_TEXT_TAG
    if "[debug]" in low or "[trace]" in low: return _MM_TEXT_DEBUG
    return _MM_TEXT_DEFAULT


class MinimapWidget(QWidget):
    LINE_H = 4
    FONT_PX = 5
    SIDE_MARGIN = 5

    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self._editor = editor
        self.setFixedWidth(140)
        self.setCursor(Qt.ArrowCursor)
        self._dragging = False
        self._drag_offset = 0.0
        self._drag_mode = "none"  # "fast" или "jump"
        self._drag_start_y = 0
        self._drag_start_line = 0
        self._drag_first_line = 0

        f = QFont()
        f.setStyleHint(QFont.Monospace)
        f.setFamily(self._editor.font().family())
        f.setPixelSize(self.FONT_PX)
        self._font = f

        editor.textChanged.connect(self.update)
        editor.updateRequest.connect(lambda *_: self.update())
        editor.verticalScrollBar().valueChanged.connect(self.update)

    def _lines_visible(self) -> int:
        return max(1, self.height() // self.LINE_H)

    def _editor_first_line(self) -> int:
        return self._editor.firstVisibleBlock().blockNumber()

    def _editor_visible_lines(self) -> int:
        fm = self._editor.fontMetrics()
        lh = max(1, fm.lineSpacing())
        return max(1, self._editor.viewport().height() // lh)

    def _minimap_top_line(self) -> int:
        N = self._editor.document().blockCount()
        M = self._lines_visible()
        E = self._editor_visible_lines()
        if N <= M or N <= E:
            return 0
        first = self._editor_first_line()
        ratio = first / (N - E)
        top = int(round(ratio * (N - M)))
        return max(0, min(N - M, top))

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.fillRect(self.rect(), QColor("#0c0f16"))

        doc = self._editor.document()
        total = doc.blockCount()
        H = self.height()
        W = self.width()
        if total == 0 or H <= 0 or W <= 0: return

        first = self._minimap_top_line()
        last = min(total, first + self._lines_visible() + 1)

        painter.setFont(self._font)
        fm = painter.fontMetrics()
        text_left = self.SIDE_MARGIN
        text_max_w = W - self.SIDE_MARGIN * 2

        block = doc.findBlockByNumber(first)
        y = 0
        while block.isValid() and block.blockNumber() < last and y < H:
            text = block.text()
            color = _minimap_line_color(text)
            painter.setPen(QColor(color))
            if text:
                avg_char_w = max(1, fm.horizontalAdvance("M"))
                max_chars = max(1, text_max_w // avg_char_w)
                painter.drawText(
                    text_left, y + self.LINE_H - 1,
                    text[:max_chars]
                )
            block = block.next()
            y += self.LINE_H

        # Прямоугольник вьюпорта
        editor_first = self._editor_first_line()
        editor_vis = self._editor_visible_lines()
        vp_top = int((editor_first - first) * self.LINE_H)
        vp_h = max(6, editor_vis * self.LINE_H)
        vp_top = max(0, min(H - vp_h, vp_top))
        
        painter.fillRect(QRect(0, vp_top, W, vp_h), QColor(255, 255, 255, 22))
        painter.setPen(QPen(QColor(255, 255, 255, 60), 1))
        painter.drawRect(QRect(0, vp_top, W - 1, max(0, vp_h - 1)))

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton: return
        y = event.position().y() if hasattr(event, "position") else event.y()

        self._drag_first_line = self._minimap_top_line()

        editor_first = self._editor_first_line()
        editor_vis = self._editor_visible_lines()
        vp_top = (editor_first - self._drag_first_line) * self.LINE_H
        vp_h = max(6, editor_vis * self.LINE_H)

        if vp_top <= y <= vp_top + vp_h:
            # Кликнули по прямоугольнику — включаем быструю прокрутку
            self._drag_mode = "fast"
            self._drag_offset = y - vp_top
            self._drag_start_y = y
            self._drag_start_line = editor_first
        else:
            # Кликнули мимо — прыгаем точно в это место (1 к 1)
            self._drag_mode = "jump"
            self._drag_offset = vp_h / 2.0
            self._scroll_to(y)
            
        self._dragging = True
        self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self._dragging:
            y = event.position().y() if hasattr(event, "position") else event.y()
            self._scroll_to(y)

    def mouseReleaseEvent(self, _event):
        self._dragging = False
        self._drag_mode = "none"
        self.setCursor(Qt.ArrowCursor)

    def _scroll_to(self, y: float):
        N = self._editor.document().blockCount()
        E = self._editor_visible_lines()
        if N <= E: return
        
        vsb = self._editor.verticalScrollBar()

        if self._drag_mode == "fast":
            # Быстрая прокрутка пропорционально всему файлу
            H = self.height()
            span = N - E
            
            # Сколько пикселей нужно протащить, чтобы пройти весь файл
            travel = max(1, H - max(6, E * self.LINE_H))
            
            dy = y - self._drag_start_y
            delta_lines = int(dy / travel * span)
            
            target = self._drag_start_line + delta_lines
            target = max(0, min(span, target))
            vsb.setValue(target)
            
        else: # jump
            target_pixel = y - self._drag_offset
            target_line = self._drag_first_line + int(target_pixel / self.LINE_H)
            target_line = max(0, min(N - E, target_line))
            vsb.setValue(target_line)


# ═══════════════════════════ Редактор ═══════════════════════════

class _LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self._editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._line_number_area = _LineNumberArea(self)
        self._minimap = MinimapWidget(self)
        self._minimap_enabled = True

        self.blockCountChanged.connect(self._update_margins)
        self.updateRequest.connect(self._on_update_request)
        self._update_margins(0)

    def minimap_enabled(self) -> bool:
        return self._minimap_enabled

    def set_minimap_enabled(self, enabled: bool) -> None:
        if enabled == self._minimap_enabled: return
        self._minimap_enabled = enabled
        self._minimap.setVisible(enabled)
        self._update_margins(0)

    def line_number_area_width(self) -> int:
        digits = max(3, len(str(max(1, self.blockCount()))))
        return 14 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_margins(self, _):
        right = self._minimap.width() if self._minimap_enabled else 0
        self.setViewportMargins(self.line_number_area_width(), 0, right, 0)

    def _on_update_request(self, rect: QRect, dy: int):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_margins(0)
        if self._minimap_enabled:
            self._minimap.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))
        if self._minimap_enabled:
            mw = self._minimap.width()
            self._minimap.setGeometry(QRect(cr.right() - mw + 1, cr.top(), mw, cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor("#0c0f16"))
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        height = self.fontMetrics().height()
        width = self._line_number_area.width() - 8
        painter.setPen(QColor("#5b6376"))
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.drawText(0, int(top), width, height, Qt.AlignRight | Qt.AlignVCenter, str(block_number + 1))
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1


# ═══════════════════════════ Панель поиска ═══════════════════════════

class _FindBar(QWidget):
    def __init__(self, editor: CodeEditor, dialog: "FileViewerDialog"):
        super().__init__(dialog)
        self.editor = editor
        self.dialog = dialog
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText("Найти…")
        self.edit.returnPressed.connect(self.find_next)
        self.case_cb = QCheckBox("Aa")
        self.case_cb.toggled.connect(self._refresh_highlight)
        self.info = QLabel("")
        self.info.setObjectName("DetailMeta")
        self.info.setMinimumWidth(80)
        self.btn_prev = QPushButton("◀")
        self.btn_prev.setObjectName("Ghost")
        self.btn_prev.setFixedWidth(34)
        self.btn_prev.clicked.connect(self.find_prev)
        self.btn_next = QPushButton("▶")
        self.btn_next.setObjectName("Ghost")
        self.btn_next.setFixedWidth(34)
        self.btn_next.clicked.connect(self.find_next)
        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("Ghost")
        self.btn_close.setFixedWidth(34)
        self.btn_close.clicked.connect(self.hide_bar)
        lay.addWidget(QLabel("Поиск:"))
        lay.addWidget(self.edit, 1)
        lay.addWidget(self.case_cb)
        lay.addWidget(self.info)
        lay.addWidget(self.btn_prev)
        lay.addWidget(self.btn_next)
        lay.addWidget(self.btn_close)
        self.edit.installEventFilter(self)
        QShortcut(QKeySequence("Escape"), self, context=Qt.WidgetWithChildrenShortcut, activated=self.hide_bar)

    def eventFilter(self, obj, event):
        if obj is self.edit and event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if event.modifiers() & Qt.ShiftModifier:
                    self.find_prev()
                else:
                    self.find_next()
                return True
        return super().eventFilter(obj, event)

    def open_bar(self, initial_text: str = ""):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            sel = cursor.selectedText()
            if sel and "\u2029" not in sel: initial_text = sel
        self.edit.setText(initial_text)
        self.edit.selectAll()
        self.show()
        self.edit.setFocus()
        self._refresh_highlight()

    def hide_bar(self):
        self.hide()
        self.dialog.set_find_selections([])
        self.editor.setFocus()

    def _flags(self) -> QTextDocument.FindFlags:
        flags = QTextDocument.FindFlags()
        if self.case_cb.isChecked(): flags |= QTextDocument.FindCaseSensitively
        return flags

    def find_next(self): self._search(backward=False)
    def find_prev(self): self._search(backward=True)

    def _search(self, backward: bool):
        text = self.edit.text()
        if not text:
            self.dialog.set_find_selections([])
            self.info.setText("")
            return
        flags = self._flags()
        if backward: flags |= QTextDocument.FindBackward
        found = self.editor.find(text, flags)
        if not found:
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.End if backward else QTextCursor.Start)
            self.editor.setTextCursor(cursor)
            found = self.editor.find(text, flags)
        if found: self.info.setText("")
        else: self.info.setText("Не найдено")
        self._refresh_highlight()

    def _refresh_highlight(self):
        text = self.edit.text()
        if not text:
            self.dialog.set_find_selections([])
            return
        sels = []
        flags = self._flags()
        cursor = QTextCursor(self.editor.document())
        cursor.movePosition(QTextCursor.Start)
        while True:
            found = self.editor.document().find(text, cursor, flags)
            if found.isNull(): break
            sel = QTextEdit.ExtraSelection()
            sel.cursor = found
            fmt = QTextCharFormat()
            fmt.setBackground(QColor("#4a3a1a"))
            fmt.setForeground(QColor("#ffd479"))
            sel.format = fmt
            sels.append(sel)
            cursor = found
        self.dialog.set_find_selections(sels)


# ═══════════════════════════ Диалог ═══════════════════════════

class FileViewerDialog(QDialog):
    def __init__(self, parent, file_name: str, content: str, pos: int, length: int,
                 on_create_rule: Optional[Callable[[str], None]] = None):
        super().__init__(parent)
        self.setWindowTitle(f"Просмотр: {file_name}")
        self.resize(1200, 800)
        self.setSizeGripEnabled(True)
        self._on_create_rule = on_create_rule

        v = QVBoxLayout(self)
        v.setContentsMargins(14, 14, 14, 14)
        v.setSpacing(10)

        head = QHBoxLayout()
        head.addWidget(section_label("Файл"))
        fname = QLabel(file_name)
        fname.setObjectName("DetailTitle")
        head.addWidget(fname)
        head.addStretch(1)
        pos_label = QLabel(f"позиция: {pos}")
        pos_label.setObjectName("DetailMeta")
        head.addWidget(pos_label)
        v.addLayout(head)

        self.editor = CodeEditor()
        self.editor.setReadOnly(True)
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.editor.setFont(_pick_mono_font())
        self.editor.setStyleSheet(
            "QPlainTextEdit {"
            " background-color: #0a0c11;"
            " color: #cfd5e3;"
            " border: 1px solid #222738;"
            " border-radius: 8px;"
            " selection-background-color: #303a5c;"
            " selection-color: #ffffff;"
            "}"
        )
        
        self.editor.setUndoRedoEnabled(False)
        self.editor.setUpdatesEnabled(False)
        self.editor.setPlainText(content)
        self.editor.setUpdatesEnabled(True)
        v.addWidget(self.editor, 1)

        self._highlighter = None
        self._content_size = len(content)

        self.chk_minimap = QCheckBox("Миникарта")
        self.chk_minimap.setChecked(True)
        self.chk_minimap.toggled.connect(self.editor.set_minimap_enabled)
        head.addWidget(self.chk_minimap)
        head.addSpacing(12)

        self.find_bar = _FindBar(self.editor, self)
        self.find_bar.hide()
        v.addWidget(self.find_bar)

        bb = QDialogButtonBox()
        btn_find = bb.addButton("Найти (Ctrl+F)", QDialogButtonBox.ActionRole)
        btn_find.setObjectName("Ghost")
        btn_find.clicked.connect(self._open_find_bar)

        btn_jump = bb.addButton("Перейти к сигнатуре", QDialogButtonBox.ActionRole)
        btn_jump.setObjectName("Ghost")
        btn_jump.clicked.connect(lambda: self._jump(pos, length))

        if on_create_rule is not None:
            btn_new = bb.addButton("Создать правило из выделения", QDialogButtonBox.ActionRole)
            btn_new.setObjectName("Primary")
            btn_new.clicked.connect(self._create_rule_from_selection)

        btn_close = bb.addButton("Закрыть", QDialogButtonBox.RejectRole)
        btn_close.setObjectName("Primary")
        bb.rejected.connect(self.reject)

        info_text = "Подсвечено место, где сработала сигнатура. Ctrl+F — поиск, F3/Shift+F3 — вперёд/назад."
        if on_create_rule is not None:
            info_text += " Выделите нужный фрагмент и нажмите «Создать правило из выделения»."
        info = QLabel(info_text)
        info.setObjectName("DetailMeta")
        info.setWordWrap(True)
        v.addWidget(info)
        v.addWidget(bb)

        QShortcut(QKeySequence("Ctrl+F"), self, context=Qt.WindowShortcut, activated=self._open_find_bar)
        QShortcut(QKeySequence("F3"), self, context=Qt.WindowShortcut, activated=self.find_bar.find_next)
        QShortcut(QKeySequence("Shift+F3"), self, context=Qt.WindowShortcut, activated=self.find_bar.find_prev)

        self._base_selections: list[QTextEdit.ExtraSelection] = []
        self._find_selections: list[QTextEdit.ExtraSelection] = []

        self._pos = pos
        self._len = length
        if pos > 0:
            QTimer.singleShot(0, lambda: self._jump(pos, length))
        else:
            self.editor.moveCursor(QTextCursor.Start)

    def _attach_highlighter(self):
        if self._highlighter is None:
            self._highlighter = MajesticLogHighlighter(self.editor.document())

    def set_find_selections(self, sels: list[QTextEdit.ExtraSelection]):
        self._find_selections = sels
        self._apply_extra_selections()

    def _apply_extra_selections(self):
        self.editor.setExtraSelections(self._base_selections + self._find_selections)

    def _open_find_bar(self):
        self.find_bar.open_bar()

    def _jump(self, pos: int, length: int):
        doc_len = max(0, self.editor.document().characterCount() - 1)
        start = max(0, min(pos, doc_len))
        end = max(start, min(pos + max(length, 1), doc_len))
        cursor = self.editor.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        self.editor.setTextCursor(cursor)
        self.editor.centerCursor()

        sel = QTextEdit.ExtraSelection()
        sel.cursor = cursor
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#4a3a1a"))
        fmt.setForeground(QColor("#ffd479"))
        sel.format = fmt
        self._base_selections = [sel]
        self._apply_extra_selections()
        self.editor.setFocus()

    def _create_rule_from_selection(self):
        if not self._on_create_rule: return
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText().replace("\u2029", "\n")
        else:
            cursor.select(QTextCursor.LineUnderCursor)
            text = cursor.selectedText().replace("\u2029", "\n")
        text = text.strip()
        if not text:
            QMessageBox.information(self, "Пусто", "Нечего выделять.")
            return
        self._on_create_rule(text)

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self)
        QTimer.singleShot(100, self._attach_highlighter)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.find_bar.isVisible():
            self.find_bar.hide_bar()
            return
        super().keyPressEvent(event)