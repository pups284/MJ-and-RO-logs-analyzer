from __future__ import annotations

SEV_MARKS = {"error": "🔴", "warning": "🟡", "info": "🔵"}

DARK_STYLE = """
* { font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 13px; outline: none; }
QMainWindow, QDialog { background-color: #0b0d13; }
QWidget { color: #e6e8ef; }
QWidget#CentralRoot { border: 2px solid transparent; border-radius: 12px; }
QWidget#CentralRoot[dragging="true"] { border: 2px dashed #6d5cff; background-color: rgba(109, 92, 255, 0.05); }
QFrame#HeaderBar { background-color: #0f121b; border: 1px solid #1c2230; border-radius: 12px; }
QLabel#AppTitle { color: #ffffff; font-size: 18px; font-weight: 800; }
QLabel#AppSubtitle { color: #8b94a3; font-size: 12px; }
QLabel#AppBadge { color: #6d5cff; font-size: 11px; font-weight: 700; background-color: rgba(109,92,255,0.14); border: 1px solid rgba(109,92,255,0.35); border-radius: 8px; padding: 3px 8px; }
QPushButton { background-color: #1c2030; color: #e6e8ef; border: 1px solid #2a3046; border-radius: 8px; padding: 7px 14px; font-weight: 500; min-height: 16px; }
QPushButton:hover { background-color: #232838; border-color: #3a4260; }
QPushButton:pressed { background-color: #171b28; }
QPushButton:disabled { color: #5b6376; background-color: #14161f; border-color: #1d2230; }
QPushButton#Primary { background-color: #6d5cff; border-color: #6d5cff; color: #ffffff; }
QPushButton#Primary:hover { background-color: #7d6eff; border-color: #7d6eff; }
QPushButton#Danger { background-color: #2a1620; border-color: #4a1f30; color: #ff8aa2; }
QPushButton#Danger:hover { background-color: #3a1c2a; border-color: #6a2a44; }
QPushButton#Ghost { background-color: transparent; border-color: #262c3f; color: #8b94a3; }
QPushButton#Ghost:hover { color: #e6e8ef; border-color: #3a4260; }
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox { background-color: #131722; border: 1px solid #262c3f; border-radius: 8px; padding: 6px 10px; color: #e6e8ef; selection-background-color: #6d5cff; selection-color: #ffffff; }
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus { border-color: #6d5cff; }
QLineEdit:read-only, QPlainTextEdit:read-only, QTextEdit:read-only { background-color: #0f1219; color: #cfd5e3; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #8b94a3; margin-right: 8px; }
QComboBox QAbstractItemView { background-color: #151823; border: 1px solid #2a3046; selection-background-color: #303a5c; color: #e6e8ef; padding: 4px; border-radius: 8px; }
QSpinBox::up-button, QSpinBox::down-button { width: 16px; background: #1c2030; border: none; }
QSpinBox::up-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-bottom: 5px solid #8b94a3; }
QSpinBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #8b94a3; }
QListWidget, QTableWidget { background-color: #10131c; border: 1px solid #222738; border-radius: 10px; padding: 4px; gridline-color: #1c2130; selection-background-color: #303a5c; selection-color: #ffffff; alternate-background-color: #0d1017; }
QListWidget::item { padding: 5px 8px; border-radius: 6px; color: #cfd5e3; }
QListWidget::item:hover { background-color: #1a2030; color: #ffffff; }
QListWidget::item:selected { background-color: #303a5c; color: #ffffff; font-weight: 600; }
QTableWidget::item { padding: 5px 8px; border: none; color: #cfd5e3; }
QTableWidget::item:hover { background-color: #1a2030; }
QTableWidget::item:selected { background-color: #303a5c; color: #ffffff; }
QHeaderView::section { background-color: #151823; color: #8b94a3; padding: 8px 10px; border: none; border-bottom: 1px solid #222738; font-weight: 600; font-size: 11px; }
QTabWidget::pane { border: 1px solid #222738; border-radius: 12px; background-color: #0d0f16; top: -1px; }
QTabBar::tab { background: transparent; color: #8b94a3; padding: 10px 22px; border: none; border-bottom: 2px solid transparent; margin-right: 4px; font-weight: 500; }
QTabBar::tab:hover { color: #e6e8ef; background-color: rgba(255,255,255,0.03); }
QTabBar::tab:selected { color: #e6e8ef; border-bottom: 2px solid #6d5cff; }
QSplitter::handle { background-color: transparent; }
QSplitter::handle:horizontal { width: 8px; }
QSplitter::handle:vertical { height: 8px; }
QSplitter::handle:hover { background-color: #222738; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #2a3046; border-radius: 5px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #3a4260; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: #2a3046; border-radius: 5px; min-width: 24px; }
QScrollBar::handle:horizontal:hover { background: #3a4260; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QStatusBar { background-color: #0d0f16; color: #8b94a3; border-top: 1px solid #1a1e2b; }
QLabel#SectionLabel { color: #8b94a3; font-size: 11px; font-weight: 700; }
QLabel#DetailTitle { color: #ffffff; font-size: 16px; font-weight: 700; }
QLabel#DetailMeta { color: #8b94a3; }
QLabel#FileInfo { background: #0c0f16; border: 1px solid #222738; border-radius: 8px; padding: 8px 10px; color: #cfd5e3; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #2a3046; border-radius: 4px; background: #131722; }
QCheckBox::indicator:checked { background: #6d5cff; border-color: #6d5cff; }
QMenu { background-color: #151823; border: 1px solid #2a3046; border-radius: 8px; padding: 6px; }
QMenu::item { padding: 6px 28px; border-radius: 6px; color: #e6e8ef; }
QMenu::item:selected { background-color: #303a5c; color: #ffffff; }
QToolTip { background-color: #1c2030; color: #e6e8ef; border: 1px solid #2a3046; border-radius: 6px; padding: 6px 8px; }
QPlainTextEdit#FileViewerText { background-color: #0a0c11; color: #d5dae5; border: 1px solid #222738; selection-background-color: #4a3a1a; selection-color: #ffd479; }
"""

LIGHT_STYLE = """
* { font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 13px; outline: none; }
QMainWindow, QDialog { background-color: #f5f6fa; }
QWidget { color: #1e2028; }
QWidget#CentralRoot { border: 2px solid transparent; border-radius: 12px; }
QWidget#CentralRoot[dragging="true"] { border: 2px dashed #6d5cff; background-color: rgba(109, 92, 255, 0.05); }
QFrame#HeaderBar { background-color: #ffffff; border: 1px solid #e1e4eb; border-radius: 12px; }
QLabel#AppTitle { color: #111319; font-size: 18px; font-weight: 800; }
QLabel#AppSubtitle { color: #6b7280; font-size: 12px; }
QLabel#AppBadge { color: #6d5cff; font-size: 11px; font-weight: 700; background-color: rgba(109,92,255,0.1); border: 1px solid rgba(109,92,255,0.3); border-radius: 8px; padding: 3px 8px; }
QPushButton { background-color: #ffffff; color: #1e2028; border: 1px solid #d1d5db; border-radius: 8px; padding: 7px 14px; font-weight: 500; min-height: 16px; }
QPushButton:hover { background-color: #f3f4f6; border-color: #9ca3af; }
QPushButton:pressed { background-color: #e5e7eb; }
QPushButton:disabled { color: #9ca3af; background-color: #f9fafb; border-color: #e5e7eb; }
QPushButton#Primary { background-color: #6d5cff; border-color: #6d5cff; color: #ffffff; }
QPushButton#Primary:hover { background-color: #5a48e8; border-color: #5a48e8; }
QPushButton#Danger { background-color: #fee2e2; border-color: #fca5a5; color: #b91c1c; }
QPushButton#Danger:hover { background-color: #fecaca; border-color: #ef4444; }
QPushButton#Ghost { background-color: transparent; border-color: #d1d5db; color: #4b5563; }
QPushButton#Ghost:hover { color: #111827; border-color: #9ca3af; }
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox { background-color: #ffffff; border: 1px solid #d1d5db; border-radius: 8px; padding: 6px 10px; color: #1e2028; selection-background-color: #6d5cff; selection-color: #ffffff; }
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus { border-color: #6d5cff; }
QLineEdit:read-only, QPlainTextEdit:read-only, QTextEdit:read-only { background-color: #f9fafb; color: #4b5563; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #6b7280; margin-right: 8px; }
QComboBox QAbstractItemView { background-color: #ffffff; border: 1px solid #d1d5db; selection-background-color: #e0e7ff; color: #1e2028; padding: 4px; border-radius: 8px; }
QSpinBox::up-button, QSpinBox::down-button { width: 16px; background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 2px; }
QSpinBox::up-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-bottom: 5px solid #6b7280; }
QSpinBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #6b7280; }
QListWidget, QTableWidget { background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 4px; gridline-color: #f3f4f6; selection-background-color: #e0e7ff; selection-color: #111827; alternate-background-color: #f9fafb; }
QListWidget::item { padding: 5px 8px; border-radius: 6px; color: #374151; }
QListWidget::item:hover { background-color: #f3f4f6; color: #111827; }
QListWidget::item:selected { background-color: #e0e7ff; color: #111827; font-weight: 600; }
QTableWidget::item { padding: 5px 8px; border: none; color: #374151; }
QTableWidget::item:hover { background-color: #f3f4f6; }
QTableWidget::item:selected { background-color: #e0e7ff; color: #111827; }
QHeaderView::section { background-color: #f9fafb; color: #6b7280; padding: 8px 10px; border: none; border-bottom: 1px solid #e5e7eb; font-weight: 600; font-size: 11px; }
QTabWidget::pane { border: 1px solid #e5e7eb; border-radius: 12px; background-color: #ffffff; top: -1px; }
QTabBar::tab { background: transparent; color: #6b7280; padding: 10px 22px; border: none; border-bottom: 2px solid transparent; margin-right: 4px; font-weight: 500; }
QTabBar::tab:hover { color: #111827; background-color: rgba(0,0,0,0.03); }
QTabBar::tab:selected { color: #111827; border-bottom: 2px solid #6d5cff; }
QSplitter::handle { background-color: transparent; }
QSplitter::handle:horizontal { width: 8px; }
QSplitter::handle:vertical { height: 8px; }
QSplitter::handle:hover { background-color: #e5e7eb; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #d1d5db; border-radius: 5px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #9ca3af; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: #d1d5db; border-radius: 5px; min-width: 24px; }
QScrollBar::handle:horizontal:hover { background: #9ca3af; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QStatusBar { background-color: #ffffff; color: #6b7280; border-top: 1px solid #e5e7eb; }
QLabel#SectionLabel { color: #6b7280; font-size: 11px; font-weight: 700; }
QLabel#DetailTitle { color: #111827; font-size: 16px; font-weight: 700; }
QLabel#DetailMeta { color: #6b7280; }
QLabel#FileInfo { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px 10px; color: #374151; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #d1d5db; border-radius: 4px; background: #ffffff; }
QCheckBox::indicator:checked { background: #6d5cff; border-color: #6d5cff; }
QMenu { background-color: #ffffff; border: 1px solid #d1d5db; border-radius: 8px; padding: 6px; }
QMenu::item { padding: 6px 28px; border-radius: 6px; color: #1e2028; }
QMenu::item:selected { background-color: #f3f4f6; color: #111827; }
QToolTip { background-color: #1e2028; color: #ffffff; border: 1px solid #374151; border-radius: 6px; padding: 6px 8px; }
QPlainTextEdit#FileViewerText { background-color: #ffffff; color: #1f2937; border: 1px solid #d1d5db; selection-background-color: #fef08a; selection-color: #854d0e; }
"""

STYLE = DARK_STYLE