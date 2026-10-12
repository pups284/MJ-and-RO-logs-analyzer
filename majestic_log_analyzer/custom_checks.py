from __future__ import annotations

import re
from typing import Callable

from .log_metadata import detect_project
from .models import Rule
from .normalization import extract_context


# Количество "Duplicate weapon item", которое считается нормой
# для каждого проекта. Если игрок на России Онлайн — 8, на Majestic — 31.
DEFAULT_DUPLICATE_EXPECTED: dict[str, int] = {
    "ro":       8,
    "majestic": 31,
}


def check_duplicate_weapon(content: str, lower: str, rule: Rule):
    lines = content.splitlines()
    suspicious = []
    for i, line in enumerate(lines):
        if "duplicate weapon item" in line.lower():
            for j in range(i, min(i + 3, len(lines))):
                m = re.search(r"First seen:\s*(\S+)", lines[j], re.I)
                if m:
                    seen = m.group(1)
                    if not re.match(r"^commoncrc:/data/ai/weapons\.meta$",
                                    seen, re.I):
                        suspicious.append((i, line, seen))
                    break
    if not suspicious:
        return None
    first_line_idx, first_line, first_seen = suspicious[0]
    pos = sum(len(l) + 1 for l in lines[:first_line_idx])
    ctx = "\n".join(f"{l}\n - First seen: {s}" for _, l, s in suspicious[:5])
    sig = "dupweapon:" + first_seen
    return ctx, sig, pos, len(first_line)


def _resolve_expected(content: str, rule: Rule) -> list[int]:
    """Возвращает список ожидаемых количеств.
    1) Если в правиле заданы count_expected — используем их.
    2) Иначе автоматически по проекту (ro → 8, majestic → 31).
    3) Если проект не определён — возвращаем []."""
    explicit = [int(x) for x in (rule.count_expected or [])
                if isinstance(x, int)]
    if explicit:
        return explicit

    proj = detect_project(content)
    if proj and proj in DEFAULT_DUPLICATE_EXPECTED:
        return [DEFAULT_DUPLICATE_EXPECTED[proj]]
    return []


def check_duplicate_count(content: str, lower: str, rule: Rule):
    """Считает вхождения rule.count_pattern и сравнивает с ожидаемым.
    Ожидаемое берётся либо из правила, либо из проекта (Connect id).
    """
    pattern = (rule.count_pattern or "").strip().lower()
    if not pattern:
        return None

    expected = _resolve_expected(content, rule)
    if not expected:
        return None

    count = lower.count(pattern)
    if count in expected:
        return None

    proj = detect_project(content)
    proj_note = ""
    if proj == "ro":
        proj_note = "  (проект: Россия Онлайн)"
    elif proj == "majestic":
        proj_note = "  (проект: Majestic RP)"

    idx = lower.find(pattern)
    if idx < 0:
        idx = 0

    header = (
        f"Найдено вхождений «{rule.count_pattern}»: {count}\n"
        f"Ожидаемые значения: {', '.join(str(x) for x in expected)}"
        f"{proj_note}"
    )
    if idx > 0:
        ctx = header + "\n\n" + extract_context(content, idx, len(pattern))
    else:
        ctx = header
    sig = f"dupcount:{count}"
    return ctx, sig, idx, len(pattern)

def check_sys_fileload_detail(content: str, lower: str, rule: Rule):
    """Для ERR_SYS_FILELOAD в client логах.

    В логе обычно есть две строки с ERR_SYS_FILELOAD:
      1) содержательная:  ERR_SYS_FILELOAD, Missing rpf: <путь> 0
      2) хвост:           ERR_SYS_FILELOAD happened. Error message: ...
    Нам нужна первая. Ищем все вхождения "err_sys_fileload," (с запятой,
    чтобы не поймать "happened") и берём последнюю содержательную строку.
    """
    # "\s*,\s*" — с запятой сразу после имени, регистр игнорируем через lower
    rx = re.compile(r"err_sys_fileload\s*,\s*\S[^\n]*", re.I)

    last_match = None
    for m in rx.finditer(lower):
        last_match = m
    if last_match is None:
        return None

    idx = last_match.start()
    # конец — до конца текущей строки, но не длиннее 300 символов
    end = content.find("\n", idx)
    if end < 0:
        end = len(content)
    if end - idx > 300:
        end = idx + 300

    # при нормализации мы уберём таймстемп и т.п., но саму строку оставим как есть
    sig = content[idx:end].rstrip()
    ctx = extract_context(content, idx, end - idx)
    return ctx, sig, idx, end - idx


CUSTOM_CHECKS: dict[str, Callable] = {
    "duplicate_weapon_mods": check_duplicate_weapon,
    "duplicate_count":       check_duplicate_count,
    "sys_fileload_detail":   check_sys_fileload_detail,
}