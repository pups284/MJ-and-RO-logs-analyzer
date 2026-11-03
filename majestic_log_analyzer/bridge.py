from __future__ import annotations

import base64
import json
import re
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


SERVER_NAME = "MajesticLogAnalyzer_SingleInstance"

ENVELOPE_PREFIX = b"MLA1\n"
PROTOCOL_VERSION = 1

MAX_REQUEST_BYTES = 128 * 1024 * 1024
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_FILES = 64

TEMP_SUBDIR = "majestic-log-analyzer"
ALLOWED_EXTENSIONS = {".log", ".txt"}


class BridgeError(Exception):
    pass


@dataclass
class InlineFile:
    name: str
    data: bytes


@dataclass
class BridgeRequest:
    paths: list[str] = field(default_factory=list)
    inline_files: list[InlineFile] = field(default_factory=list)
    auto_open: bool = False
    source: str = "local"


def temp_dir() -> Path:
    directory = Path(tempfile.gettempdir()) / TEMP_SUBDIR
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def safe_filename(name: str, fallback: str = "discord.log") -> str:
    candidate = (name or "").replace("\\", "/").rsplit("/", 1)[-1]
    candidate = re.sub(r"[^\w\-. ()]+", "_", candidate, flags=re.UNICODE).strip(" .")
    candidate = candidate[:180] or fallback
    if Path(candidate).suffix.lower() not in ALLOWED_EXTENSIONS:
        candidate += ".log"
    return candidate


def is_log_name(name: str) -> bool:
    lowered = (name or "").lower()
    if Path(lowered).suffix in ALLOWED_EXTENSIONS:
        return True
    base = lowered.rsplit(".", 1)[0]
    return base.startswith(("main", "client", "patcher", "cef", "service"))


def encode_open_paths(paths: list[str], *, auto_open: bool = False,
                      source: str = "local") -> bytes:
    payload = {
        "version": PROTOCOL_VERSION,
        "type": "open_logs",
        "source": source,
        "auto_open": bool(auto_open),
        "files": [{"name": Path(p).name, "path": str(p)} for p in paths if p],
    }
    return ENVELOPE_PREFIX + json.dumps(payload, ensure_ascii=False).encode("utf-8")


def _decode_inline(entry: dict, index: int) -> Optional[InlineFile]:
    name = entry.get("name")
    if not isinstance(name, str) or not name.strip():
        raise BridgeError(f"files[{index}]: name is required")

    if "content_base64" in entry:
        raw = entry["content_base64"]
        if not isinstance(raw, str):
            raise BridgeError(f"files[{index}]: content_base64 must be a string")
        try:
            data = base64.b64decode(raw, validate=True)
        except Exception as exc:
            raise BridgeError(f"files[{index}]: invalid base64 ({exc})") from exc
    elif "content" in entry:
        raw = entry["content"]
        if not isinstance(raw, str):
            raise BridgeError(f"files[{index}]: content must be a string")
        data = raw.encode("utf-8")
    else:
        return None

    if len(data) > MAX_FILE_BYTES:
        raise BridgeError(f"files[{index}]: file is too large")
    return InlineFile(name=name, data=data)


def parse_request(raw: bytes) -> BridgeRequest:
    if len(raw) > MAX_REQUEST_BYTES:
        raise BridgeError("request is too large")

    stripped = raw.lstrip(b"\xef\xbb\xbf \t\r\n")
    if not stripped:
        return BridgeRequest()

    if stripped.startswith(ENVELOPE_PREFIX):
        stripped = stripped[len(ENVELOPE_PREFIX):]
    elif not stripped.startswith(b"{"):
        paths = [p for p in raw.decode("utf-8", errors="replace").split("\0") if p]
        return BridgeRequest(paths=paths, auto_open=False, source="legacy")

    try:
        payload = json.loads(stripped.decode("utf-8"))
    except Exception as exc:
        raise BridgeError(f"invalid JSON payload: {exc}") from exc

    if not isinstance(payload, dict):
        raise BridgeError("payload must be a JSON object")
    if payload.get("type", "open_logs") != "open_logs":
        raise BridgeError("unsupported request type")

    entries = payload.get("files") or []
    if not isinstance(entries, list):
        raise BridgeError("files must be a list")
    if len(entries) > MAX_FILES:
        raise BridgeError("too many files")

    paths: list[str] = []
    inline_files: list[InlineFile] = []
    for index, entry in enumerate(entries):
        if isinstance(entry, str):
            paths.append(entry)
            continue
        if not isinstance(entry, dict):
            raise BridgeError(f"files[{index}]: expected object or string")

        path = entry.get("path")
        if isinstance(path, str) and path.strip():
            paths.append(path)
            continue

        inline = _decode_inline(entry, index)
        if inline is not None:
            inline_files.append(inline)

    auto_open = payload.get("auto_open", True)
    source = payload.get("source", "bridge")
    return BridgeRequest(
        paths=paths,
        inline_files=inline_files,
        auto_open=bool(auto_open),
        source=str(source)[:64],
    )


def materialize(inline_files: list[InlineFile]) -> list[str]:
    if not inline_files:
        return []

    directory = temp_dir()
    written: list[str] = []
    for item in inline_files:
        safe = safe_filename(item.name)
        destination = directory / f"bridge_{uuid.uuid4().hex}_{safe}"
        try:
            destination.write_bytes(item.data)
        except OSError as exc:
            raise BridgeError(f"cannot save {safe}: {exc}") from exc
        written.append(str(destination))
    return written
