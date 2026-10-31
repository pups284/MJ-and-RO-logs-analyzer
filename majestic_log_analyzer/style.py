from __future__ import annotations

from string import Template

from PySide6.QtGui import QFont, QFontDatabase


SEV_MARKS = {"error": "\u25cf", "warning": "\u25cf", "info": "\u25cf"}

SPACE = {
    "xxs": 2,
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "xxl": 32,
}

RADIUS = {
    "sm": 6,
    "md": 8,
    "lg": 10,
    "xl": 14,
}

_FONT_FAMILY = (
    "'Inter', 'Manrope', 'Golos Text', 'Segoe UI Variable Text', "
    "'Segoe UI', 'Helvetica Neue', sans-serif"
)
_MONO_FAMILY = (
    "'JetBrains Mono', 'Cascadia Mono', 'Cascadia Code', "
    "'Consolas', 'Courier New', monospace"
)

DARK_TOKENS = {
    "font_family": _FONT_FAMILY,
    "mono_family": _MONO_FAMILY,
    "font_size": "13px",
    "micro_size": "10px",
    "bg": "#101114",
    "sidebar": "#151619",
    "card": "#1B1D21",
    "surface": "#22252A",
    "surface_hover": "#282C31",
    "surface_pressed": "#1C1F23",
    "border": "#2B2E34",
    "border_strong": "#383C43",
    "text": "#F2F3F5",
    "muted": "#9297A1",
    "faint": "#6F747E",
    "accent": "#C71A4E",
    "accent_hover": "#D9245B",
    "accent_pressed": "#A81540",
    "accent_soft": "rgba(199, 26, 78, 0.14)",
    "accent_border": "rgba(199, 26, 78, 0.42)",
    "accent_disabled_bg": "#4A2231",
    "accent_disabled_text": "#B98A9A",
    "success": "#5E9E76",
    "success_soft": "rgba(94, 158, 118, 0.13)",
    "warning": "#C9863F",
    "warning_soft": "rgba(201, 134, 63, 0.13)",
    "error": "#C25858",
    "error_soft": "rgba(194, 88, 88, 0.13)",
    "error_soft_hover": "rgba(194, 88, 88, 0.20)",
    "input_bg": "#16181C",
    "row_alt": "rgba(255, 255, 255, 0.018)",
    "disabled_text": "#5C616A",
    "disabled_bg": "#17191D",
    "scroll": "#383C43",
    "scroll_hover": "#4A4F57",
    "code_bg": "#0C0D10",
    "code_text": "#D9DCE1",
    "code_selection_bg": "#4A3A1A",
    "code_selection_text": "#FFD479",
    "radius_sm": f"{RADIUS['sm']}px",
    "radius_md": f"{RADIUS['md']}px",
    "radius_lg": f"{RADIUS['lg']}px",
    "radius_xl": f"{RADIUS['xl']}px",
}

LIGHT_TOKENS = {
    "font_family": _FONT_FAMILY,
    "mono_family": _MONO_FAMILY,
    "font_size": "13px",
    "micro_size": "10px",
    "bg": "#F2F3F5",
    "sidebar": "#E9EBEF",
    "card": "#FFFFFF",
    "surface": "#F4F5F7",
    "surface_hover": "#ECEFF3",
    "surface_pressed": "#E4E7EB",
    "border": "#DCE0E5",
    "border_strong": "#C5CBD3",
    "text": "#1B1D21",
    "muted": "#626871",
    "faint": "#858B94",
    "accent": "#B31645",
    "accent_hover": "#9C123B",
    "accent_pressed": "#861034",
    "accent_soft": "rgba(179, 22, 69, 0.10)",
    "accent_border": "rgba(179, 22, 69, 0.35)",
    "accent_disabled_bg": "#E4C9D3",
    "accent_disabled_text": "#8E566A",
    "success": "#3E7C58",
    "success_soft": "rgba(62, 124, 88, 0.10)",
    "warning": "#9A651F",
    "warning_soft": "rgba(154, 101, 31, 0.10)",
    "error": "#A63D3D",
    "error_soft": "rgba(166, 61, 61, 0.09)",
    "error_soft_hover": "rgba(166, 61, 61, 0.15)",
    "input_bg": "#FFFFFF",
    "row_alt": "rgba(0, 0, 0, 0.015)",
    "disabled_text": "#A0A6AE",
    "disabled_bg": "#F7F8F9",
    "scroll": "#C5CBD3",
    "scroll_hover": "#A9B0B9",
    "code_bg": "#F7F8FA",
    "code_text": "#2A2E34",
    "code_selection_bg": "#FEF08A",
    "code_selection_text": "#854D0E",
    "radius_sm": f"{RADIUS['sm']}px",
    "radius_md": f"{RADIUS['md']}px",
    "radius_lg": f"{RADIUS['lg']}px",
    "radius_xl": f"{RADIUS['xl']}px",
}


_QSS = Template(
    """
* {
    font-family: $font_family;
    font-size: $font_size;
    outline: 0;
}
QMainWindow, QDialog {
    background-color: $bg;
}
QWidget {
    color: $text;
}
QWidget#AppShell, QWidget#ContentArea {
    background-color: $bg;
}

QFrame#Sidebar {
    background-color: $sidebar;
    border: none;
    border-right: 1px solid $border;
}
QFrame#SidebarCard {
    background-color: $card;
    border: 1px solid $border;
    border-radius: $radius_md;
}
QFrame#SidebarRule, QFrame#Rule {
    background-color: $border;
    border: none;
    min-height: 1px;
    max-height: 1px;
}
QFrame#Card {
    background-color: $card;
    border: 1px solid $border;
    border-radius: $radius_lg;
}
QFrame#StatChip {
    background-color: $card;
    border: 1px solid $border;
    border-radius: $radius_md;
}

QLabel#BrandName {
    color: $text;
    font-size: 15px;
    font-weight: 700;
}
QLabel#BrandKind {
    color: $faint;
    font-size: 9px;
    font-weight: 600;
}
QLabel#SidebarSection {
    color: $faint;
    font-size: 10px;
    font-weight: 600;
    padding: 0 8px;
}
QLabel#SidebarStatusTitle {
    color: $muted;
    font-size: 11px;
    font-weight: 600;
}
QLabel#SidebarStatusText {
    color: $faint;
    font-size: 10px;
}
QLabel#SidebarDot {
    color: $success;
    font-size: 12px;
}
QLabel#PageTitle {
    color: $text;
    font-size: 21px;
    font-weight: 700;
}
QLabel#PageSubtitle {
    color: $muted;
    font-size: 12px;
}
QLabel#StatCaption {
    color: $faint;
    font-size: 9px;
    font-weight: 600;
}
QLabel#StatValue {
    color: $text;
    font-size: 14px;
    font-weight: 700;
}
QLabel#SectionLabel {
    color: $faint;
    font-size: $micro_size;
    font-weight: 600;
}
QLabel#CountBadge {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 9px;
    color: $muted;
    padding: 1px 7px;
    font-size: $micro_size;
    font-weight: 600;
}
QLabel#HintBar {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: $radius_md;
    color: $muted;
    padding: 10px 12px;
}
QLabel#DetailTitle {
    color: $text;
    font-size: 17px;
    font-weight: 700;
}
QLabel#DetailMeta {
    color: $muted;
    font-size: 12px;
}
QLabel#DialogTitle {
    color: $text;
    font-size: 19px;
    font-weight: 700;
}
QLabel#DialogSubtitle {
    color: $muted;
    font-size: 12px;
}
QLabel#FileInfo {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: $radius_sm;
    padding: 9px 10px;
    color: $muted;
}

QPushButton {
    background-color: $surface;
    color: $text;
    border: 1px solid $border;
    border-radius: $radius_sm;
    padding: 6px 13px;
    min-height: 18px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: $surface_hover;
    border-color: $border_strong;
}
QPushButton:pressed {
    background-color: $surface_pressed;
}
QPushButton:focus {
    border-color: $accent_border;
}
QPushButton:disabled {
    color: $disabled_text;
    background-color: $disabled_bg;
    border-color: $border;
}
QPushButton#Primary {
    background-color: $accent;
    border-color: $accent;
    color: #FFFFFF;
    font-weight: 600;
}
QPushButton#Primary:hover {
    background-color: $accent_hover;
    border-color: $accent_hover;
}
QPushButton#Primary:pressed {
    background-color: $accent_pressed;
    border-color: $accent_pressed;
}
QPushButton#Primary:disabled {
    background-color: $accent_disabled_bg;
    border-color: $accent_disabled_bg;
    color: $accent_disabled_text;
}
QPushButton#Danger {
    background-color: $error_soft;
    border-color: $accent_border;
    color: $error;
}
QPushButton#Danger:hover {
    background-color: $error_soft_hover;
    border-color: $error;
}
QPushButton#Danger:pressed {
    background-color: $error_soft;
}
QPushButton#Ghost {
    background-color: transparent;
    border-color: $border;
    color: $muted;
}
QPushButton#Ghost:hover {
    background-color: $surface;
    border-color: $border_strong;
    color: $text;
}
QPushButton#Ghost:pressed {
    background-color: $surface_pressed;
}
QPushButton#IconButton {
    background-color: transparent;
    border: 1px solid $border;
    border-radius: $radius_sm;
    padding: 0;
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
}
QPushButton#IconButton:hover {
    background-color: $surface;
    border-color: $border_strong;
}
QPushButton#NavButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: $radius_md;
    color: $muted;
    padding: 8px 10px;
    text-align: left;
    font-weight: 500;
    min-height: 20px;
}
QPushButton#NavButton:hover {
    background-color: $surface;
    color: $text;
}
QPushButton#NavButton:checked {
    background-color: $accent_soft;
    border-color: $accent_border;
    color: $text;
    font-weight: 600;
}
QPushButton#NavButton:pressed {
    background-color: $surface_pressed;
}
QPushButton#NavButton[compact="true"] {
    padding: 9px;
    text-align: center;
}

QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {
    background-color: $input_bg;
    border: 1px solid $border;
    border-radius: $radius_sm;
    padding: 6px 9px;
    color: $text;
    selection-background-color: $accent;
    selection-color: #FFFFFF;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: $accent;
}
QLineEdit:read-only, QPlainTextEdit:read-only, QTextEdit:read-only {
    background-color: $surface;
    color: $muted;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid $muted;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: $card;
    border: 1px solid $border_strong;
    color: $text;
    selection-background-color: $accent_soft;
    selection-color: $text;
    padding: 4px;
    border-radius: $radius_sm;
}
QSpinBox::up-button, QSpinBox::down-button {
    width: 17px;
    background: $surface;
    border: none;
}
QSpinBox::up-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid $muted;
}
QSpinBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid $muted;
}

QListWidget, QTableWidget {
    background-color: $card;
    border: 1px solid $border;
    border-radius: $radius_md;
    padding: 4px;
    gridline-color: $border;
    selection-background-color: $accent_soft;
    selection-color: $text;
    alternate-background-color: $row_alt;
}
QListWidget#FlatList, QTableWidget#FlatTable {
    background-color: transparent;
    border: none;
    padding: 0;
}
QListWidget::item {
    padding: 7px 9px;
    border-radius: $radius_sm;
    color: $text;
}
QListWidget::item:hover {
    background-color: $surface;
}
QListWidget::item:selected {
    background-color: $accent_soft;
    color: $text;
    font-weight: 600;
}
QTableWidget::item {
    padding: 6px 9px;
    border: none;
    color: $text;
}
QTableWidget::item:hover {
    background-color: $surface;
}
QTableWidget::item:selected {
    background-color: $accent_soft;
    color: $text;
}
QHeaderView::section {
    background-color: $surface;
    color: $muted;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid $border;
    font-weight: 600;
    font-size: $micro_size;
}
QTableCornerButton::section {
    background-color: $surface;
    border: none;
}

QTabWidget::pane {
    border: none;
    background: transparent;
}
QTabBar {
    background: transparent;
    qproperty-drawBase: 0;
}
QTabBar::tab {
    background: transparent;
    color: $muted;
    padding: 6px 13px;
    border: 1px solid transparent;
    border-radius: $radius_sm;
    margin-right: 4px;
    font-weight: 500;
}
QTabBar::tab:hover {
    color: $text;
    background-color: $surface;
}
QTabBar::tab:selected {
    color: $text;
    background-color: $surface;
    border-color: $border;
    font-weight: 600;
}
QTabWidget#MainTabs::pane {
    border: none;
    background: transparent;
}
QTabWidget#InnerTabs::pane {
    border: none;
    background: transparent;
}

QSplitter::handle {
    background-color: transparent;
}
QSplitter::handle:horizontal {
    width: 12px;
}
QSplitter::handle:vertical {
    height: 12px;
}
QSplitter::handle:hover {
    background-color: $border;
    border-radius: 2px;
}

QScrollBar:vertical {
    background: transparent;
    width: 9px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: $scroll;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: $scroll_hover;
}
QScrollBar:horizontal {
    background: transparent;
    height: 9px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: $scroll;
    border-radius: 4px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover {
    background: $scroll_hover;
}
QScrollBar::add-line, QScrollBar::sub-line {
    height: 0;
    width: 0;
}
QScrollBar::add-page, QScrollBar::sub-page {
    background: transparent;
}

QStatusBar {
    background-color: $sidebar;
    color: $faint;
    border-top: 1px solid $border;
    padding: 0 8px;
}
QStatusBar::item {
    border: none;
}

QScrollArea {
    background: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}
QCheckBox {
    spacing: 8px;
    color: $muted;
}
QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border: 1px solid $border_strong;
    border-radius: 4px;
    background: $input_bg;
}
QCheckBox::indicator:hover {
    border-color: $accent;
}
QCheckBox::indicator:checked {
    background: $accent;
    border-color: $accent;
}
QMenu {
    background-color: $card;
    border: 1px solid $border_strong;
    border-radius: $radius_sm;
    padding: 6px;
}
QMenu::item {
    padding: 7px 26px;
    border-radius: 5px;
    color: $text;
}
QMenu::item:selected {
    background-color: $surface;
    color: $text;
}
QMenu::separator {
    height: 1px;
    background: $border;
    margin: 5px 8px;
}
QToolTip {
    background-color: $surface;
    color: $text;
    border: 1px solid $border_strong;
    border-radius: 6px;
    padding: 6px 8px;
}
QPlainTextEdit#FileViewerText {
    background-color: $code_bg;
    color: $code_text;
    border: 1px solid $border;
    border-radius: $radius_md;
    padding: 8px;
    selection-background-color: $code_selection_bg;
    selection-color: $code_selection_text;
}
QWidget#FindBar {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: $radius_md;
}
QProgressBar {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 3px;
    color: $muted;
    text-align: center;
    min-height: 6px;
    max-height: 6px;
}
QProgressBar::chunk {
    background-color: $accent;
    border-radius: 2px;
}
QProgressBar#TutorialProgress {
    min-height: 4px;
    max-height: 4px;
    border: none;
    background-color: $border;
}
QProgressBar#TutorialProgress::chunk {
    background-color: $accent;
    border-radius: 2px;
}
QFrame#TutorialCard {
    background-color: $card;
    border: 1px solid $border_strong;
    border-radius: $radius_xl;
}
QMessageBox {
    background-color: $bg;
}
"""
)

DARK_STYLE = _QSS.substitute(DARK_TOKENS)
LIGHT_STYLE = _QSS.substitute(LIGHT_TOKENS)
STYLE = DARK_STYLE


def theme_tokens(theme: str = "dark") -> dict:
    return LIGHT_TOKENS if theme == "light" else DARK_TOKENS


def severity_color(theme: str, severity: str) -> str:
    tokens = theme_tokens(theme)
    if severity == "error":
        return tokens["error"]
    if severity == "warning":
        return tokens["warning"]
    if severity == "info":
        return tokens["muted"]
    return tokens["faint"]


def apply_app_font(app) -> None:
    families = set(QFontDatabase.families())
    for name in ("Inter", "Manrope", "Golos Text", "Segoe UI Variable Text", "Segoe UI"):
        if name in families:
            font = QFont(name)
            font.setPointSizeF(9.75)
            app.setFont(font)
            return
