from __future__ import annotations

import urllib.request
from pathlib import Path

from PySide6.QtCore import QThread, Signal

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/pups284/MJ-and-RO-logs-analyzer/main/data/"

class DownloadWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, target_dir: Path):
        super().__init__()
        self.target_dir = target_dir

    def run(self):
        try:
            self.target_dir.mkdir(parents=True, exist_ok=True)
            files = ["rules.json", "notes.json"]
            for fname in files:
                url = GITHUB_RAW_BASE + fname
                dest = self.target_dir / fname
                tmp = dest.with_suffix(".tmp")
                req = urllib.request.Request(url, headers={"User-Agent": "MajesticLogAnalyzer"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read()
                tmp.write_bytes(data)
                tmp.replace(dest)
            self.finished.emit(True, "")
        except Exception as e:
            self.finished.emit(False, str(e))