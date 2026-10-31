from __future__ import annotations
import re

_RE_TS_FULL  = re.compile(r"\[\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?\]")
_RE_TS_SHORT = re.compile(r"\[\d{1,2}:\d{2}:\d{2}(?:\.\d+)?\]")
_RE_TS_BARE  = re.compile(r"\b\d{1,2}:\d{2}:\d{2}(?:\.\d+)?\b")
_RE_UUID     = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
_RE_HEX      = re.compile(r"\b0x[0-9a-f]{4,}\b", re.I)
_RE_WS       = re.compile(r"\s+")


def normalize_signature(s: str) -> str:
    if not s:
        return ""
    s = _RE_TS_FULL.sub("[]", s)
    s = _RE_TS_SHORT.sub("[]", s)
    s = _RE_TS_BARE.sub("", s)
    s = _RE_UUID.sub("<uuid>", s)
    s = _RE_HEX.sub("<addr>", s)
    s = _RE_WS.sub(" ", s).strip()
    return s


def detect_log_type(name: str) -> str:
    n = name.lower()
    if n in ("main.log", "main.old.log") or n.startswith("main"):
        return "main"
    if "patcher" in n:
        return "patcher"
    if n.startswith("client"):
        return "client"
    if n.startswith("service"):
        return "service"
    if n.startswith("cef"):
        return "cef"
    return "any"


def extract_context(content: str, idx: int, length: int) -> str:
    lines = content.splitlines(keepends=True)
    pos = 0
    line_idx = 0
    for i, ln in enumerate(lines):
        if pos + len(ln) >= idx:
            line_idx = i
            break
        pos += len(ln)
        
    start = max(0, line_idx - 2)
    end = min(len(lines), line_idx + 3)
    
    return "".join(lines[start:end]).replace("\r", "")

SESSION_MARKER = "(startup)"


def find_session_start(content: str) -> int:
    lower = content.lower()
    idx = lower.rfind(SESSION_MARKER.lower())
    if idx < 0:
        return 0
    line_start = content.rfind("\n", 0, idx)
    return line_start + 1 if line_start >= 0 else 0