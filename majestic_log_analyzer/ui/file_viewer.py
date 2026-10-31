from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import (
    QEvent, QRect, QSize, Qt, QTimer, QRegularExpression, Signal,
)
from PySide6.QtGui import (
    QColor, QFont, QFontDatabase, QKeySequence, QPainter, QPen,
    QShortcut, QSyntaxHighlighter, QTextCharFormat, QTextCursor,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDialogButtonBox, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton,
    QTextEdit, QVBoxLayout, QWidget,
)

from ..platform_win import apply_dark_title_bar
from ..style import SPACE, theme_tokens
from .common import card_frame, section_label


_MONO_CANDIDATES = (
    "Cascadia Mono", "Cascadia Code", "JetBrains Mono",
    "Consolas", "Courier New", "Menlo", "Monaco", "DejaVu Sans Mono",
)


def _pick_mono_font() -> QFont:
    families = set(QFontDatabase.families())
    font = QFont()
    font.setFamily(next(
        (name for name in _MONO_CANDIDATES if name in families), "monospace"
    ))
    font.setStyleHint(QFont.Monospace)
    font.setFixedPitch(True)
    font.setPointSizeF(10.0)
    return font


class MajesticLogHighlighter(QSyntaxHighlighter):
    VISIBLE_MARGIN = 40

    def __init__(self, document: QTextDocument, editor: "CodeEditor"):
        super().__init__(document)
        self._editor = editor
        theme = QApplication.instance().property("theme") or "dark"
        tokens = theme_tokens(theme)

        self.fmt_ts      = self._fmt(tokens["faint"])
        self.fmt_warn    = self._fmt(tokens["warning"])
        self.fmt_err     = self._fmt(tokens["error"], bold=True)
        self.fmt_tag     = self._fmt(tokens["accent"])
        self.fmt_ok_txt  = self._fmt(tokens["success"])
        self.fmt_err_txt = self._fmt(tokens["error"])
        self.fmt_neutral = self._fmt(tokens["muted"])
        self.fmt_server  = self._fmt(tokens["muted"])
        self.fmt_info    = self._fmt(tokens["muted"])

        self.re_ts = QRegularExpression(r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\]|\[\d{2}:\d{2}:\d{2}(?:\.\d{3})?\]")
        self.re_warn = QRegularExpression(r"\[(?:warn|warning|debug|trace)\]|\bERR_[A-Z0-9_]+\b|'(?:TIMEOUT|NETWORK|ABORTED)'")
        self.re_err = QRegularExpression(r"\[(?:Error|ERROR|Warning|WARNING)\]|\b(?:error|Error|ERROR|fatal|Fatal|FATAL|critical|Critical|CRITICAL|crashed|failed|exception)\b")
        self.re_tag = QRegularExpression(r"\[\s*\([\w.\-]+\)\s*\]|\[(?:MAJESTIC|LAUNCH|GAME|BACKUP|CRASH|DOWNLOADER|REVALIDATE|HASHMAP|REQUEST|HOSTING|AUTH|DOWNLOAD|DISKS|DISPLAY|EMAIL|EPIC|FSR|INIT|MACRO|MASTERLIST|MIGRATE|MODSLIST|PERMISSIONS|QUEUE|RGL|SECURE|SIGN_IN|SIGN_UP|STEAM|TRUSTED_DEVICES|UPDATER|WEB|CHECKFILE|CLOTHES|DC|AUTH_HISTORY|MODSCATEGORIESLIST|NEW_PASSWORD|hooks|web|net|voice|res|sync|discord|gui|js|assets|render|hooks\.pool|hooks\.ped|res\.download|js\.script)\]|\bMAJESTIC:")
        self.re_ok = QRegularExpression(r"\bsuccess:\s*true\b|\b(?:ok|success|initialized|loaded|completed)\b|\btrue\b")
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
        if not text: return

        first_visible = self._editor.firstVisibleBlock().blockNumber()
        block_number = self.currentBlock().blockNumber()
        last_visible = first_visible + self._editor.visible_line_count()
        margin = self.VISIBLE_MARGIN
        if (block_number < first_visible - margin
                or block_number > last_visible + margin * 2):
            return

        low = text.lower()

        if "[" in text:
            it = self.re_ts.globalMatch(text)
            while it.hasNext():
                m = it.next(); self.setFormat(m.capturedStart(), m.capturedLength(), self.fmt_ts)
        if "[info]" in low:
            it = self.re_info.globalMatch(text)
            while it.hasNext():
                m = it.next(); self.setFormat(m.capturedStart(), m.capturedLength(), self.fmt_info)
        if "warn" in low or "debug" in low or "trace" in low or "err_" in low or "timeout" in low or "network" in low or "aborted" in low:
            it = self.re_warn.globalMatch(text)
            while it.hasNext():
                m = it.next(); self.setFormat(m.capturedStart(), m.capturedLength(), self.fmt_warn)
        if "error" in low or "fatal" in low or "critical" in low or "crashed" in low or "failed" in low or "exception" in low or "[warning]" in low:
            it = self.re_err.globalMatch(text)
            while it.hasNext():
                m = it.next(); self.setFormat(m.capturedStart(), m.capturedLength(), self.fmt_err)
        if "(" in text or "majestic" in low:
            it = self.re_tag.globalMatch(text)
            while it.hasNext():
                m = it.next(); self.setFormat(m.capturedStart(), m.capturedLength(), self.fmt_tag)
        if "true" in low or "ok" in low or "success" in low or "loaded" in low or "initialized" in low:
            it = self.re_ok.globalMatch(text)
            while it.hasNext():
                m = it.next(); self.setFormat(m.capturedStart(), m.capturedLength(), self.fmt_ok_txt)
        if "false" in low or "null" in low or "undefined" in low:
            it = self.re_neutral.globalMatch(text)
            while it.hasNext():
                m = it.next(); self.setFormat(m.capturedStart(), m.capturedLength(), self.fmt_neutral)
        if "ru" in low or "miami" in low or "tverskoy" in low:
            it = self.re_server.globalMatch(text)
            while it.hasNext():
                m = it.next(); self.setFormat(m.capturedStart(), m.capturedLength(), self.fmt_server)


def _minimap_line_color(text: str) -> str:
    if not text:
        return "#2E3444"
    low = text.lower()
    theme = QApplication.instance().property("theme") or "dark"
    tokens = theme_tokens(theme)

    if ("err_" in low or "[error]" in low or "\"error\"" in low or "'error'" in low
            or " fatal" in low or " crashed" in low or "failed:" in low or " failed" in low):
        return tokens["error"]
    if "[warn" in low:
        return tokens["warning"]
    if "success" in low or "loaded" in low or " ok " in f" {low} ":
        return tokens["success"]
    if "majestic:" in low or "(patcher)" in low or "(client)" in low:
        return tokens["accent"]
    if "[debug]" in low or "[trace]" in low:
        return tokens["faint"]
    return tokens["muted"]


class MinimapWidget(QWidget):
    LINE_H = 3
    SIDE_MARGIN = 5

    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self._editor = editor
        self.setFixedWidth(140)
        self.setCursor(Qt.ArrowCursor)
        self._dragging = False
        self._drag_offset = 0.0
        self._drag_mode = "none"
        self._drag_start_y = 0
        self._drag_start_line = 0
        self._drag_first_line = 0

        editor.updateRequest.connect(lambda *_: self.update())
        editor.verticalScrollBar().valueChanged.connect(self.update)

    def _lines_visible(self) -> int:
        return max(1, self.height() // self.LINE_H)

    def _editor_first_line(self) -> int:
        return self._editor.firstVisibleBlock().blockNumber()

    def _minimap_top_line(self) -> int:
        N = self._editor.document().blockCount()
        M = self._lines_visible()
        E = self._editor.visible_line_count()
        if N <= M or N <= E: return 0
        first = self._editor_first_line()
        ratio = first / (N - E)
        top = int(round(ratio * (N - M)))
        return max(0, min(N - M, top))

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        
        theme = QApplication.instance().property("theme") or "dark"
        tokens = theme_tokens(theme)
        painter.fillRect(self.rect(), QColor(tokens["code_bg"]))

        doc = self._editor.document()
        total = doc.blockCount()
        H = self.height()
        W = self.width()
        if total == 0 or H <= 0 or W <= 0: return

        max_len = self._editor.max_line_length
        first = self._minimap_top_line()
        last = min(total, first + self._lines_visible() + 1)

        block = doc.findBlockByNumber(first)
        y = 0
        while block.isValid() and block.blockNumber() < last and y < H:
            text = block.text()
            color = _minimap_line_color(text)
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(color))
            
            text_len = len(text)
            if text_len > 0:
                w = min(W - 10, max(4, int((text_len / max_len) * (W - 10))))
                painter.drawRect(5, y + 1, w, self.LINE_H - 1)

            block = block.next()
            y += self.LINE_H

        editor_first = self._editor_first_line()
        editor_vis = self._editor.visible_line_count()
        vp_top = int((editor_first - first) * self.LINE_H)
        vp_h = max(6, editor_vis * self.LINE_H)
        vp_top = max(0, min(H - vp_h, vp_top))
        
        painter.fillRect(
            QRect(0, vp_top, W, vp_h),
            QColor(255, 255, 255, 34) if theme == "dark" else QColor(0, 0, 0, 18),
        )
        painter.setPen(
            QPen(
                QColor(0, 0, 0, 70) if theme == "light" else QColor(255, 255, 255, 52),
                1,
            )
        )
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(QRect(0, vp_top, W - 1, max(0, vp_h - 1)))

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton: return
        y = event.position().y() if hasattr(event, "position") else event.y()

        self._drag_first_line = self._minimap_top_line()
        editor_first = self._editor_first_line()
        editor_vis = self._editor.visible_line_count()
        vp_top = (editor_first - self._drag_first_line) * self.LINE_H
        vp_h = max(6, editor_vis * self.LINE_H)

        if vp_top <= y <= vp_top + vp_h:
            self._drag_mode = "fast"
            self._drag_offset = y - vp_top
            self._drag_start_y = y
            self._drag_start_line = editor_first
        else:
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
        E = self._editor.visible_line_count()
        if N <= E: return
        vsb = self._editor.verticalScrollBar()

        if self._drag_mode == "fast":
            H = self.height()
            span = N - E
            travel = max(1, H - max(6, E * self.LINE_H))
            dy = y - self._drag_start_y
            delta_lines = int(dy / travel * span)
            target = self._drag_start_line + delta_lines
            target = max(0, min(span, target))
            vsb.setValue(target)
        else:
            target_pixel = y - self._drag_offset
            target_line = self._drag_first_line + int(target_pixel / self.LINE_H)
            target_line = max(0, min(N - E, target_line))
            vsb.setValue(target_line)


class LazyLogEditor(QPlainTextEdit):
    CHUNK_SIZE = 20000
    JUMP_BACK = 3000
    JUMP_AHEAD = 6000

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_lines: list[str] = []
        self._loaded_start = 0
        self._loaded_end = 0
        self._max_line_length = 100
        self._is_loading = False

        self.verticalScrollBar().valueChanged.connect(self._on_scroll)
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

    @property
    def max_line_length(self) -> int:
        return self._max_line_length

    @property
    def loaded_start(self) -> int:
        return self._loaded_start

    def visible_line_count(self) -> int:
        line_height = max(1, self.fontMetrics().lineSpacing())
        return max(1, self.viewport().height() // line_height)

    def _replace_window(self, start: int, end: int) -> None:
        self._is_loading = True
        try:
            self.setPlainText("\n".join(self._all_lines[start:end]))
            self._loaded_start = start
            self._loaded_end = end
        finally:
            self._is_loading = False

    def load_lines(self, lines: list[str]) -> None:
        self._all_lines = lines
        self._max_line_length = max(100, max(map(len, lines), default=0))
        self._replace_window(0, min(len(lines), self.CHUNK_SIZE))
        self.moveCursor(QTextCursor.Start)

    def _char_to_line(self, char_pos: int) -> tuple[int, int]:
        if char_pos <= 0 or not self._all_lines:
            return 0, 0

        offset = 0
        for index, line in enumerate(self._all_lines):
            next_offset = offset + len(line) + 1
            if char_pos < next_offset:
                return index, char_pos - offset
            offset = next_offset

        last = len(self._all_lines) - 1
        return last, len(self._all_lines[last])

    def jump_to_char(self, char_pos: int) -> int:
        line_index, line_offset = self._char_to_line(char_pos)
        start = max(0, line_index - self.JUMP_BACK)
        end = min(len(self._all_lines), line_index + self.JUMP_AHEAD)
        self._replace_window(start, end)

        local_line_index = line_index - start
        block = self.document().findBlockByNumber(local_line_index)
        if not block.isValid():
            return 0
            
        line_text = self._all_lines[line_index]
        prefix_text = line_text[:line_offset]
        
        utf16_offset = len(prefix_text.encode('utf-16-le')) // 2
        
        return block.position() + utf16_offset

    def _append_lines(self) -> None:
        end = min(len(self._all_lines), self._loaded_end + self.CHUNK_SIZE)
        if end == self._loaded_end:
            return
        chunk = "\n".join(self._all_lines[self._loaded_end:end])
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.End)
        cursor.insertText("\n" + chunk)
        self._loaded_end = end

    def _prepend_lines(self) -> None:
        start = max(0, self._loaded_start - self.CHUNK_SIZE)
        if start == self._loaded_start:
            return

        added = self._loaded_start - start
        chunk = "\n".join(self._all_lines[start:self._loaded_start]) + "\n"
        scrollbar = self.verticalScrollBar()
        old_value = scrollbar.value()

        self._is_loading = True
        try:
            cursor = QTextCursor(self.document())
            cursor.movePosition(QTextCursor.Start)
            cursor.insertText(chunk)
            self._loaded_start = start
            scrollbar.setValue(old_value + added)
        finally:
            self._is_loading = False

    def _on_scroll(self, value: int) -> None:
        if self._is_loading:
            return

        scrollbar = self.verticalScrollBar()
        if (value >= scrollbar.maximum() - 100
                and self._loaded_end < len(self._all_lines)):
            self._load_next_chunk()
        elif value <= 100 and self._loaded_start > 0:
            self._load_prev_chunk()

    def _load_next_chunk(self) -> None:
        self._is_loading = True
        try:
            scrollbar = self.verticalScrollBar()
            was_at_bottom = scrollbar.value() >= scrollbar.maximum() - 20
            self._append_lines()
            if was_at_bottom:
                scrollbar.setValue(scrollbar.maximum())
        finally:
            self._is_loading = False

    def _load_prev_chunk(self) -> None:
        self._prepend_lines()


class _LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self._editor.line_number_area_paint_event(event)


class CodeEditor(LazyLogEditor):
    visible_area_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._line_number_area = _LineNumberArea(self)
        self._minimap = MinimapWidget(self)
        self._minimap_enabled = True

        self.blockCountChanged.connect(self._update_margins)
        self.updateRequest.connect(self._on_update_request)
        self._update_margins(0)

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
        self.visible_area_changed.emit()

    def line_number_area_paint_event(self, event):
        painter = QPainter(self._line_number_area)
        theme = QApplication.instance().property("theme") or "dark"
        tokens = theme_tokens(theme)

        painter.fillRect(event.rect(), QColor(tokens["code_bg"]))
        text_color = tokens["faint"]
        block = self.firstVisibleBlock()
        block_number = block.blockNumber() + self._loaded_start
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        height = self.fontMetrics().height()
        width = self._line_number_area.width() - 8
        painter.setPen(QColor(text_color))
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.drawText(0, int(top), width, height, Qt.AlignRight | Qt.AlignVCenter, str(block_number + 1))
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1


class _FindBar(QWidget):
    def __init__(self, editor: CodeEditor, dialog: "FileViewerWindow"):
        super().__init__(dialog)
        self.setObjectName("FindBar")
        self.editor = editor
        self.dialog = dialog
        lay = QHBoxLayout(self)
        lay.setContentsMargins(SPACE["sm"], SPACE["sm"], SPACE["sm"], SPACE["sm"])
        lay.setSpacing(SPACE["sm"])
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
            theme = QApplication.instance().property("theme") or "dark"
            tokens = theme_tokens(theme)
            fmt.setBackground(QColor(tokens["code_selection_bg"]))
            fmt.setForeground(QColor(tokens["code_selection_text"]))
            sel.format = fmt
            sels.append(sel)
            cursor = found
        self.dialog.set_find_selections(sels)


class FileViewerWindow(QMainWindow):
    def __init__(self, file_name: str, content: str, pos: int, length: int,
                 on_create_rule: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.setWindowTitle(f"Просмотр: {file_name}")
        self.resize(1200, 800)
        self.setMinimumSize(900, 620)
        self.setWindowIcon(QApplication.instance().windowIcon())
        self._on_create_rule = on_create_rule

        central = QWidget()
        central.setObjectName("ContentArea")
        self.setCentralWidget(central)

        v = QVBoxLayout(central)
        v.setContentsMargins(
            SPACE["xl"], SPACE["lg"] + 2, SPACE["xl"], SPACE["lg"]
        )
        v.setSpacing(SPACE["md"])

        header = card_frame()
        head = QHBoxLayout(header)
        head.setContentsMargins(SPACE["lg"], SPACE["md"], SPACE["lg"], SPACE["md"])
        head.setSpacing(SPACE["lg"])

        file_box = QVBoxLayout()
        file_box.setContentsMargins(0, 0, 0, 0)
        file_box.setSpacing(1)
        file_box.addWidget(section_label("Файл"))
        fname = QLabel(file_name)
        fname.setObjectName("DetailTitle")
        fname.setWordWrap(True)
        file_box.addWidget(fname)
        head.addLayout(file_box, 1)

        pos_label = QLabel(f"ПОЗИЦИЯ {pos}")
        pos_label.setObjectName("StatCaption")
        head.addWidget(pos_label, 0, Qt.AlignTop)

        self.chk_minimap = QCheckBox("Миникарта")
        self.chk_minimap.setChecked(True)
        head.addWidget(self.chk_minimap, 0, Qt.AlignVCenter)
        v.addWidget(header)

        self.editor = CodeEditor()
        self.editor.setObjectName("FileViewerText")
        self.editor.setFont(_pick_mono_font())
        self.editor.setUndoRedoEnabled(False)
        self.chk_minimap.toggled.connect(self.editor.set_minimap_enabled)

        QApplication.setOverrideCursor(Qt.WaitCursor)
        lines = content.splitlines()
        self.editor.load_lines(lines)
        QApplication.restoreOverrideCursor()

        editor_card = card_frame()
        ec = QVBoxLayout(editor_card)
        ec.setContentsMargins(SPACE["sm"], SPACE["sm"], SPACE["sm"], SPACE["sm"])
        ec.addWidget(self.editor)
        v.addWidget(editor_card, 1)

        self._highlighter = None
        self._highlight_timer = QTimer(self)
        self._highlight_timer.setSingleShot(True)
        self._highlight_timer.setInterval(60)
        self._highlight_timer.timeout.connect(self._refresh_visible_highlight)
        self.editor.verticalScrollBar().valueChanged.connect(
            lambda *_: self._highlight_timer.start()
        )
        self.editor.visible_area_changed.connect(self._highlight_timer.start)

        self.find_bar = _FindBar(self.editor, self)
        self.find_bar.hide()
        v.insertWidget(1, self.find_bar)

        footer = card_frame()
        fv = QVBoxLayout(footer)
        fv.setContentsMargins(SPACE["lg"], SPACE["md"], SPACE["lg"], SPACE["md"])
        fv.setSpacing(SPACE["sm"])

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
        btn_close.setObjectName("Ghost")
        bb.rejected.connect(self.close)

        info_text = "Подсвечено место, где сработала сигнатура. Ctrl+F — поиск, F3/Shift+F3 — вперёд/назад."
        if on_create_rule is not None:
            info_text += " Выделите нужный фрагмент и нажмите «Создать правило из выделения»."
        info = QLabel(info_text)
        info.setObjectName("DetailMeta")
        info.setWordWrap(True)
        fv.addWidget(info)
        fv.addWidget(bb)
        v.addWidget(footer)

        QShortcut(QKeySequence("Ctrl+F"), self, context=Qt.WindowShortcut, activated=self._open_find_bar)
        QShortcut(QKeySequence("F3"), self, context=Qt.WindowShortcut, activated=self.find_bar.find_next)
        QShortcut(QKeySequence("Shift+F3"), self, context=Qt.WindowShortcut, activated=self.find_bar.find_prev)

        self._base_selections: list[QTextEdit.ExtraSelection] = []
        self._find_selections: list[QTextEdit.ExtraSelection] = []

        if pos > 0:
            QTimer.singleShot(100, self, lambda: self._jump(pos, length))
        else:
            self.editor.moveCursor(QTextCursor.Start)

    def _attach_highlighter(self):
        if self._highlighter is None:
            self._highlighter = MajesticLogHighlighter(
                self.editor.document(), self.editor
            )
            self._highlight_timer.start()

    def _refresh_visible_highlight(self):
        if self._highlighter is None:
            return
        block = self.editor.firstVisibleBlock()
        count = (self.editor.visible_line_count()
                 + MajesticLogHighlighter.VISIBLE_MARGIN)
        for _ in range(count):
            if not block.isValid():
                break
            self._highlighter.rehighlightBlock(block)
            block = block.next()
        self.editor.viewport().update()

    def set_find_selections(self, sels: list[QTextEdit.ExtraSelection]):
        self._find_selections = sels
        self._apply_extra_selections()

    def _apply_extra_selections(self):
        self.editor.setExtraSelections(self._base_selections + self._find_selections)

    def _open_find_bar(self):
        self.find_bar.open_bar()

    def _jump(self, pos: int, length: int):
        rel_pos = self.editor.jump_to_char(pos)
        
        doc_len = max(0, self.editor.document().characterCount() - 1)
        start = max(0, min(rel_pos, doc_len))
        
        cursor = self.editor.textCursor()
        cursor.setPosition(start)
        
        end = min(start + max(length, 1), doc_len)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        
        self.editor.setTextCursor(cursor)
        self.editor.centerCursor()

        sel = QTextEdit.ExtraSelection()
        sel.cursor = cursor
        fmt = QTextCharFormat()
        theme = QApplication.instance().property("theme") or "dark"
        tokens = theme_tokens(theme)
        fmt.setBackground(QColor(tokens["code_selection_bg"]))
        fmt.setForeground(QColor(tokens["code_selection_text"]))
        sel.format = fmt
        self._base_selections = [sel]
        self._find_selections = []
        self._apply_extra_selections()
        self._attach_highlighter()
        self._highlight_timer.start()
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

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() != QEvent.StyleChange:
            return
        if getattr(self, "_highlighter", None) is not None:
            self._highlighter.setDocument(None)
            self._highlighter.deleteLater()
            self._highlighter = None
            self._attach_highlighter()
        if getattr(self, "editor", None) is not None:
            self.editor._minimap.update()
        if getattr(self, "find_bar", None) is not None and self.find_bar.isVisible():
            self.find_bar._refresh_highlight()

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self)
        QTimer.singleShot(300, self, self._attach_highlighter)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.find_bar.isVisible():
            self.find_bar.hide_bar()
            return
        super().keyPressEvent(event)