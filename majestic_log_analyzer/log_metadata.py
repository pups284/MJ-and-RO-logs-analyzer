from __future__ import annotations

import re

# main.log:
#   gtaPlatform: 'steam',
#   gtaPath: 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Grand Theft Auto V',
_RE_PLATFORM = re.compile(r"gtaPlatform:\s*'([^']+)'")
_RE_GTA_PATH = re.compile(r"gtaPath:\s*'([^']+)'")

# client.log:
#   [20:42:40.315][hooks] Game path: D:\GTAV
#   [20:42:27.001] Connect id: ro2
_RE_GAME_PATH = re.compile(r"Game\s+path\s*[:=]\s*(.+?)(?:\r?\n|$)", re.I)
_RE_CONNECT_ID = re.compile(r"Connect\s+id\s*[:=]\s*(ro|ru)\s*(\d+)", re.I)


PLATFORM_LABELS = {
    "steam":      "Steam",
    "epic-games": "Epic Games",
    "epic":       "Epic Games",
    "rockstar":   "Rockstar",
}


def _unescape_win_path(p: str) -> str:
    """В main.log пути в одинарных кавычках с двойными бэкслэшами
    (это JSON-строка внутри лога). Разуплотняем '\\\\' → '\\'."""
    return p.replace("\\\\", "\\")


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] in "\"'" and s[-1] == s[0]:
        return s[1:-1]
    return s


def extract_main_metadata(content: str) -> dict:
    meta: dict = {}
    m = _RE_PLATFORM.search(content)
    if m:
        plat = m.group(1).strip().lower()
        meta["gta_platform"] = plat
        meta["gta_platform_label"] = PLATFORM_LABELS.get(plat, plat)

    m = _RE_GTA_PATH.search(content)
    if m:
        meta["gta_path"] = _unescape_win_path(m.group(1).strip())
    return meta


def detect_project(content: str) -> str | None:
    """Возвращает 'ro' (Россия Онлайн) или 'majestic' (Majestic RP),
    либо None, если строки Connect id нет."""
    m = _RE_CONNECT_ID.search(content)
    if not m:
        return None
    return "ro" if m.group(1).lower() == "ro" else "majestic"


def extract_client_metadata(content: str) -> dict:
    meta: dict = {}
    m = _RE_GAME_PATH.search(content)
    if m:
        meta["game_path"] = _strip_quotes(m.group(1))

    proj = detect_project(content)
    if proj:
        meta["project"] = proj
        meta["project_label"] = (
            "Россия Онлайн" if proj == "ro" else "Majestic RP"
        )
    return meta


def extract_metadata(file_name: str, content: str) -> dict:
    n = file_name.lower()
    if n.startswith("main"):
        return extract_main_metadata(content)
    if n.startswith("client"):
        return extract_client_metadata(content)
    return {}


def format_metadata(meta: dict) -> str:
    """Человекочитаемое представление для UI и тултипов."""
    if not meta:
        return ""
    lines: list[str] = []
    if meta.get("gta_platform_label"):
        lines.append(f"Платформа: {meta['gta_platform_label']}")
    if meta.get("project_label"):
        lines.append(f"Проект: {meta['project_label']}")
    if meta.get("gta_path"):
        lines.append(f"Папка GTA V: {meta['gta_path']}")
    if meta.get("game_path"):
        lines.append(f"Папка игры: {meta['game_path']}")
    return "\n".join(lines)


def short_metadata_tag(meta: dict) -> str:
    """Короткий суффикс для строки в списке файлов."""
    if not meta:
        return ""
    if meta.get("gta_platform_label"):
        return meta["gta_platform_label"]
    if meta.get("project_label"):
        return meta["project_label"]
    return ""