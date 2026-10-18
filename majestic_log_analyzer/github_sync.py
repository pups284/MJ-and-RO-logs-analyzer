from __future__ import annotations

import json

from PySide6.QtCore import QObject, Signal, QUrl, QTimer
from PySide6.QtNetwork import (
    QNetworkAccessManager, QNetworkRequest, QNetworkReply,
)

from .models import Rule, Note

BASE_URL = "https://raw.githubusercontent.com/pups284/MJ-and-RO-logs-analyzer/main/data/"


def merge_rules(local: list[Rule], remote: list[Rule]) -> list[Rule]:
    remote_by_id = {r.id: r for r in remote}
    local_ids = {r.id for r in local}
    merged = [remote_by_id.get(r.id, r) for r in local]
    for r in remote:
        if r.id not in local_ids:
            merged.append(r)
    return merged


def merge_notes(local: list[Note], remote: list[Note]) -> list[Note]:
    remote_by_id = {n.id: n for n in remote}
    remote_keys = {(n.rule_id, n.signature, n.kind): n for n in remote}
    local_ids = {n.id for n in local}
    local_keys = {(n.rule_id, n.signature, n.kind) for n in local}

    merged: list[Note] = []
    for n in local:
        if n.id in remote_by_id:
            merged.append(remote_by_id[n.id])
        elif (n.rule_id, n.signature, n.kind) in remote_keys:
            continue
        else:
            merged.append(n)
    for n in remote:
        if n.id in local_ids:
            continue
        if (n.rule_id, n.signature, n.kind) in local_keys:
            continue
        merged.append(n)
    return merged


class GitHubSync(QObject):
    finished = Signal(bool, str, list, list)

    def __init__(self, target: str, current_rules: list[Rule],
                 current_notes: list[Note], parent=None):
        super().__init__(parent)
        self.nam = QNetworkAccessManager(self)
        self.target = target
        self.current_rules = current_rules
        self.current_notes = current_notes
        self.replies: list[QNetworkReply] = []
        self.remote_data: dict[str, list] = {}
        self._finished = False

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(
            lambda: self._fail("Превышено время ожидания ответа от GitHub (15 сек).")
        )
        self.timer.start(15000)

    def start(self) -> None:
        if self.target == "rules":
            self._fetch("rules.json")
        elif self.target == "notes":
            self._fetch("notes.json")
        elif self.target == "exceptions":
            self._fetch("exceptions.json")

    def _fetch(self, filename: str) -> None:
        url = QUrl(BASE_URL + filename)
        req = QNetworkRequest(url)
        req.setHeader(QNetworkRequest.UserAgentHeader, "MajesticLogAnalyzer")
        reply = self.nam.get(req)
        self.replies.append(reply)
        reply.finished.connect(lambda r=reply, f=filename: self._on_reply(r, f))

    def _on_reply(self, reply: QNetworkReply, filename: str) -> None:
        if self._finished:
            return

        if reply.error() != QNetworkReply.NetworkError.NoError:
            # Если exceptions.json нет на GitHub — подтягиваем notes.json (совместимость)
            if filename == "exceptions.json" and reply.error() == QNetworkReply.NetworkError.ContentNotFoundError:
                reply.deleteLater()
                if reply in self.replies:
                    self.replies.remove(reply)
                self._fetch("notes.json")
                return
            self._fail(f"Ошибка сети ({filename}): {reply.errorString()}")
            return

        try:
            data = json.loads(reply.readAll().data().decode("utf-8"))
        except Exception as e:
            self._fail(f"Ошибка парсинга {filename}: {e}")
            return

        self.remote_data[filename] = data
        reply.deleteLater()
        if reply in self.replies:
            self.replies.remove(reply)
        if not self.replies:
            self._finish_success()

    def _finish_success(self) -> None:
        if self._finished:
            return
        self._finished = True
        self.timer.stop()

        try:
            if self.target == "rules":
                remote_rules = [Rule.from_dict(r) for r in self.remote_data.get("rules.json", [])]
                final_rules = merge_rules(self.current_rules, remote_rules)
                self.finished.emit(True, "", final_rules, self.current_notes)

            elif self.target == "notes":
                # Тянем ТОЛЬКО примечания
                remote_dicts = self.remote_data.get("notes.json", [])
                remote_notes = [Note.from_dict(n) for n in remote_dicts if n.get("kind") != "ignore"]
                
                local_notes = [n for n in self.current_notes if n.kind != "ignore"]
                local_exceptions = [n for n in self.current_notes if n.kind == "ignore"]
                
                merged_notes = merge_notes(local_notes, remote_notes)
                self.finished.emit(True, "", self.current_rules, merged_notes + local_exceptions)

            elif self.target == "exceptions":
                # Тянем ТОЛЬКО исключения
                remote_dicts = self.remote_data.get("exceptions.json", [])
                if not remote_dicts and "notes.json" in self.remote_data:
                    remote_dicts = [n for n in self.remote_data["notes.json"] if n.get("kind") == "ignore"]

                for d in remote_dicts:
                    d["kind"] = "ignore"
                remote_exceptions = [Note.from_dict(n) for n in remote_dicts]

                local_notes = [n for n in self.current_notes if n.kind != "ignore"]
                local_exceptions = [n for n in self.current_notes if n.kind == "ignore"]

                merged_exceptions = merge_notes(local_exceptions, remote_exceptions)
                self.finished.emit(True, "", self.current_rules, local_notes + merged_exceptions)

        except Exception as e:
            self.finished.emit(False, f"Ошибка слияния: {e}", [], [])

    def _fail(self, msg: str) -> None:
        if self._finished:
            return
        self._finished = True
        self.timer.stop()
        for r in list(self.replies):
            r.abort()
            r.deleteLater()
        self.replies.clear()
        self.finished.emit(False, msg, [], [])