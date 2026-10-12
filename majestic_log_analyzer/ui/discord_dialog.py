from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QVBoxLayout,
)

from ..discord_import import DiscordError, download_logs_from_url
from ..platform_win import apply_dark_title_bar
from ..storage import load_settings, save_settings
from .common import section_label


class DiscordImportDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Импорт логов из Discord")
        self.resize(680, 520)
        self.setSizeGripEnabled(True)

        self.downloaded: list[tuple[str, str]] = []  # (path, original_name)

        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(10)

        settings = load_settings()

        # ── Токен ──
        v.addWidget(section_label("Токен бота"))
        token_row = QHBoxLayout()
        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.Password)
        self.token_edit.setPlaceholderText("Bot-токен из Discord Developer Portal")
        self.token_edit.setText(settings.get("discord_token", ""))
        btn_show = QPushButton("👁")
        btn_show.setObjectName("Ghost")
        btn_show.setFixedWidth(38)
        btn_show.setCheckable(True)
        btn_show.toggled.connect(
            lambda on: self.token_edit.setEchoMode(
                QLineEdit.Normal if on else QLineEdit.Password
            )
        )
        token_row.addWidget(self.token_edit, 1)
        token_row.addWidget(btn_show)
        v.addLayout(token_row)

        hint_token = QLabel(
            "Бот должен быть на том же сервере, что и сообщение, "
            "и иметь право «Read Message History» в этом канале. "
            "Токен сохраняется локально в data/settings.json."
        )
        hint_token.setObjectName("DetailMeta")
        hint_token.setWordWrap(True)
        v.addWidget(hint_token)

        # ── Ссылка ──
        v.addWidget(section_label("Ссылка на сообщение"))
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText(
            "https://discord.com/channels/<server>/<channel>/<message>"
        )
        v.addWidget(self.url_edit)

        # ── Опции ──
        self.allow_any = QCheckBox("Скачивать любые вложения (не только .log/.txt)")
        v.addWidget(self.allow_any)

        # ── Лог ──
        v.addWidget(section_label("Журнал"))
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(150)
        v.addWidget(self.log_view)

        note = QLabel(
            "Файлы сохраняются в %TEMP%/majestic-log-analyzer и "
            "удаляются автоматически при «Очистить» или при закрытии программы."
        )
        note.setObjectName("DetailMeta")
        note.setWordWrap(True)
        v.addWidget(note)

        # ── Кнопки ──
        bb = QDialogButtonBox()
        self.btn_download = bb.addButton(
            "Скачать и проанализировать", QDialogButtonBox.AcceptRole
        )
        self.btn_download.setObjectName("Primary")
        btn_close = bb.addButton("Закрыть", QDialogButtonBox.RejectRole)
        bb.accepted.connect(self._on_download)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def _log(self, text: str):
        self.log_view.appendPlainText(text)

    def _on_download(self):
        token = self.token_edit.text().strip()
        url = self.url_edit.text().strip()
        if not token:
            QMessageBox.warning(self, "Токен", "Укажите токен бота.")
            return
        if not url:
            QMessageBox.warning(self, "Ссылка", "Укажите ссылку на сообщение.")
            return

        s = load_settings()
        s["discord_token"] = token
        save_settings(s)

        self.log_view.clear()
        self.btn_download.setEnabled(False)
        try:
            files = download_logs_from_url(
                url, token,
                allow_non_logs=self.allow_any.isChecked(),
                progress=self._log,
            )
        except DiscordError as e:
            self._log(f"Ошибка: {e}")
            QMessageBox.warning(self, "Ошибка", str(e))
            self.btn_download.setEnabled(True)
            return
        except Exception as e:
            self._log(f"Неожиданная ошибка: {e}")
            QMessageBox.warning(self, "Ошибка", str(e))
            self.btn_download.setEnabled(True)
            return

        self.downloaded = [(str(p), name) for p, name in files]
        self._log(f"Готово: скачано {len(files)} файл(ов).")
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self)