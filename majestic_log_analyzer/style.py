from __future__ import annotations

SEV_COLORS = {"error": "#ff5470", "warning": "#ffb547", "info": "#4dd0e1"}
SEV_MARKS  = {"error": "🔴", "warning": "🟡", "info": "🔵"}


STYLE = """
* {
    font-family: 'Segoe UI', 'Inter', 'SF Pro Text', 'Roboto', sans-serif;
    font-size: 13px;
    outline: none;
}
QMainWindow, QDialog { background-color: #0b0d13; }
QWidget { color: #e6e8ef; }

/* ── Рамка при перетаскивании файлов ── */
QWidget#CentralRoot {
    border: 2px solid transparent;
    border-radius: 12px;
}
QWidget#CentralRoot[dragging="true"] {
    border: 2px dashed #6d5cff;
    background-color: rgba(109, 92, 255, 0.05);
}

QFrame#HeaderBar {
    background-color: #0f121b;
    border: 1px solid #1c2230;
    border-radius: 12px;
}
QLabel#AppTitle { color: #ffffff; font-size: 18px; font-weight: 800; }
QLabel#AppSubtitle { color: #8b94a3; font-size: 12px; }
QLabel#AppBadge {
    color: #6d5cff; font-size: 11px; font-weight: 700;
    background-color: rgba(109,92,255,0.14);
    border: 1px solid rgba(109,92,255,0.35);
    border-radius: 8px; padding: 3px 8px;
}

/* ── Buttons ── */
QPushButton {
    background-color: #1c2030; color: #e6e8ef;
    border: 1px solid #2a3046; border-radius: 8px;
    padding: 7px 14px; font-weight: 500; min-height: 16px;
}
QPushButton:hover { background-color: #232838; border-color: #3a4260; }
QPushButton:pressed { background-color: #171b28; }
QPushButton:disabled { color: #5b6376; background-color: #14161f; border-color: #1d2230; }
QPushButton:focus {
    border-color: #6d5cff;
}
QPushButton#Primary {
    background-color: #6d5cff; border-color: #6d5cff; color: #ffffff;
}
QPushButton#Primary:hover { background-color: #7d6eff; border-color: #7d6eff; }
QPushButton#Primary:pressed { background-color: #5a48e8; }
QPushButton#Primary:focus { border-color: #a99bff; }
QPushButton#Danger {
    background-color: #2a1620; border-color: #4a1f30; color: #ff8aa2;
}
QPushButton#Danger:hover { background-color: #3a1c2a; border-color: #6a2a44; }
QPushButton#Danger:focus { border-color: #ff8aa2; }
QPushButton#Ghost {
    background-color: transparent; border-color: #262c3f; color: #8b94a3;
}
QPushButton#Ghost:hover { color: #e6e8ef; border-color: #3a4260; }
QPushButton::menu-indicator {
    subcontrol-origin: padding; subcontrol-position: right center; right: 6px;
}

/* ── Inputs ── */
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {
    background-color: #131722; border: 1px solid #262c3f; border-radius: 8px;
    padding: 6px 10px; color: #e6e8ef;
    selection-background-color: #6d5cff; selection-color: #ffffff;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus,
QSpinBox:focus, QComboBox:focus { border-color: #6d5cff; }
QLineEdit:read-only, QPlainTextEdit:read-only, QTextEdit:read-only {
    background-color: #0f1219; color: #cfd5e3;
}
QComboBox::drop-down { border: none; width: 22px; }
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #8b94a3;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #151823; border: 1px solid #2a3046;
    selection-background-color: #303a5c; color: #e6e8ef;
    padding: 4px; border-radius: 8px;
}

/* ── Lists & Tables: заметная подсветка выбранного ── */
QListWidget, QTableWidget {
    background-color: #10131c; border: 1px solid #222738; border-radius: 10px;
    padding: 4px; gridline-color: #1c2130;
    selection-background-color: #303a5c; selection-color: #ffffff;
    alternate-background-color: #0d1017;
}
QListWidget:focus, QTableWidget:focus { border-color: #3a4260; }

QListWidget::item {
    padding: 7px 10px;
    border-radius: 6px;
    color: #cfd5e3;
}
QListWidget::item:hover { background-color: #1a2030; color: #ffffff; }
QListWidget::item:selected {
    background-color: #303a5c;
    color: #ffffff;
    font-weight: 600;
}
QListWidget::item:selected:hover { background-color: #3a4770; }
QListWidget::item:selected:!active {
    background-color: #262e4a;
    color: #d5dae5;
}

QTableWidget::item {
    padding: 6px 10px;
    border: none;
    color: #cfd5e3;
}
QTableWidget::item:hover { background-color: #1a2030; }
QTableWidget::item:selected {
    background-color: #303a5c;
    color: #ffffff;
}
QTableWidget::item:selected:!active {
    background-color: #262e4a;
    color: #d5dae5;
}

QHeaderView::section {
    background-color: #151823; color: #8b94a3;
    padding: 8px 10px; border: none;
    border-bottom: 1px solid #222738;
    font-weight: 600; font-size: 11px;
}
QHeaderView::section:checked { background-color: #1a2030; color: #cfd5e3; }
QTableCornerButton::section { background-color: #151823; border: none; }

/* ── Tabs ── */
QTabWidget::pane {
    border: 1px solid #222738; border-radius: 12px;
    background-color: #0d0f16; top: -1px;
}
QTabBar::tab {
    background: transparent; color: #8b94a3;
    padding: 10px 22px; border: none;
    border-bottom: 2px solid transparent;
    margin-right: 4px; font-weight: 500;
}
QTabBar::tab:hover { color: #e6e8ef; background-color: rgba(255,255,255,0.03); }
QTabBar::tab:selected { color: #e6e8ef; border-bottom: 2px solid #6d5cff; }

/* ── Splitters ── */
QSplitter::handle { background-color: transparent; }
QSplitter::handle:horizontal { width: 8px; }
QSplitter::handle:vertical   { height: 8px; }
QSplitter::handle:hover { background-color: #222738; }

/* ── Scrollbars ── */
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #2a3046; border-radius: 5px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #3a4260; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: #2a3046; border-radius: 5px; min-width: 24px; }
QScrollBar::handle:horizontal:hover { background: #3a4260; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

/* ── Status bar ── */
QStatusBar {
    background-color: #0d0f16; color: #8b94a3;
    border-top: 1px solid #1a1e2b;
}
QStatusBar::item { border: none; }

/* ── Labels ── */
QLabel#SectionLabel { color: #8b94a3; font-size: 11px; font-weight: 700; }
QLabel#DetailTitle { color: #ffffff; font-size: 16px; font-weight: 700; }
QLabel#DetailMeta  { color: #8b94a3; }

/* ── Checkbox ── */
QCheckBox { spacing: 8px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #2a3046; border-radius: 4px; background: #131722;
}
QCheckBox::indicator:checked { background: #6d5cff; border-color: #6d5cff; }
QCheckBox::indicator:hover { border-color: #6d5cff; }

/* ── Menu ── */
QMenu {
    background-color: #151823; border: 1px solid #2a3046;
    border-radius: 8px; padding: 6px;
}
QMenu::item { padding: 6px 28px 6px 28px; border-radius: 6px; color: #e6e8ef; }
QMenu::item:selected { background-color: #303a5c; color: #ffffff; }
QMenu::separator { height: 1px; background: #222738; margin: 4px 8px; }
QMenu::indicator { width: 14px; height: 14px; margin-left: 8px; }
QMenu::indicator:checked { background: #6d5cff; border-radius: 3px; }

/* ── Tooltip ── */
QToolTip {
    background-color: #1c2030; color: #e6e8ef;
    border: 1px solid #2a3046; border-radius: 6px; padding: 6px 8px;
}

/* ── Фокус-подсветка у читаемых полей ── */
QPlainTextEdit#FileViewerText {
    background-color: #0a0c11;
    color: #d5dae5;
    border: 1px solid #222738;
    selection-background-color: #4a3a1a;
    selection-color: #ffd479;
}
QPlainTextEdit#FileViewerText:focus { border-color: #6d5cff; }
"""