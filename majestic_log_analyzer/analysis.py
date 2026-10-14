from __future__ import annotations

import re
from typing import Optional

from .custom_checks import CUSTOM_CHECKS
from .models import Finding, Note, Rule
from .normalization import (
    detect_log_type, extract_context, find_session_start, normalize_signature,
)


def rule_matches(rule: Rule, lower: str, content: str):
    if rule.all_of:
        for s in rule.all_of:
            if s.lower() not in lower:
                return None
    if rule.any_of:
        if not any(s.lower() in lower for s in rule.any_of):
            return None
    if rule.none_of:
        for s in rule.none_of:
            if s.lower() in lower:
                return None
    if rule.custom_check:
        fn = CUSTOM_CHECKS.get(rule.custom_check)
        if fn:
            return fn(content, lower, rule)
        return None

    if rule.block_pattern:
        try:
            rex = re.compile(rule.block_pattern, re.I | re.S)
            m = rex.search(content)
            if m:
                ctx = m.group(0)
                # если в матче есть переводы строк, берём только первую
                first_line = ctx.split("\n", 1)[0]
                sig = first_line[:200]
                return ctx, sig, m.start(), m.end() - m.start()
        except re.error:
            pass

    primary = (rule.all_of or rule.any_of or [""])[0]
    if primary:
        # Сначала ищем «содержательное» вхождение: primary + запятая.
        # Например, для правила с primary="err_sys_fileload" это отсеет
        # строку-хвост "ERR_SYS_FILELOAD happened. Error message: ..."
        # и оставит содержательную "ERR_SYS_FILELOAD, Missing rpf: ...".
        idx = -1
        primary_low = primary.lower()
        primary_comma_low = primary_low + ","

        # 1) пробуем "primary," снизу вверх
        if primary_comma_low != primary_low:
            idx = lower.rfind(primary_comma_low)

        # 2) если такой формы нет — откатываемся на «голое» вхождение
        if idx < 0:
            idx = lower.rfind(primary_low)

        if idx >= 0:
            ctx = extract_context(content, idx, len(primary))
            # сигнатура — от начала совпадения до конца строки,
            # но не длиннее 300 символов
            end = content.find("\n", idx)
            if end < 0 or end - idx > 300:
                end = idx + 300
            return ctx, content[idx:end], idx, len(primary)
    return None

def pick_notes(notes: list[Note], rule_id: str, sig: str) -> list[Note]:
    """Все заметки, подходящие под (rule_id, signature). Может быть много."""
    return [n for n in notes if n.rule_id == rule_id and n.signature == sig]


def find_duplicate_note(
    notes: list[Note],
    rule_id: str,
    sig: str,
    kind: str,
    exclude_id: Optional[str] = None,
    match_pattern: str = "",   # оставлен для совместимости, игнорируется
) -> Optional[Note]:
    for n in notes:
        if exclude_id is not None and n.id == exclude_id:
            continue
        if n.rule_id == rule_id and n.signature == sig and n.kind == kind:
            return n
    return None


def analyze(files: list[tuple[str, str]],
            rules: list[Rule],
            notes: list[Note]) -> list[Finding]:
    findings: list[Finding] = []
    for fname, content in files:
        ltype = detect_log_type(fname)

        # Анализируем только последнюю сессию.
        # Для логов без маркера (client/patcher/…) — весь файл.
        region_start = find_session_start(content)
        region = content[region_start:]
        lower = region.lower()

        for rule in rules:
            if rule.log_type not in ("any", ltype):
                continue
            res = rule_matches(rule, lower, region)
            if not res:
                continue
            ctx, raw_sig, rel_pos, match_len = res
            sig = normalize_signature(raw_sig)
            matching_notes = pick_notes(notes, rule.id, sig)
            is_ignored = any(n.kind == "ignore" for n in matching_notes)
            if not rule.enabled:
                continue
            findings.append(Finding(
                rule_id=rule.id, rule_name=rule.name,
                severity=rule.severity, category=rule.category,
                file_name=fname, log_type=ltype,
                context=ctx, signature=sig,
                explanation=rule.explanation, suggestion=rule.suggestion,
                faq_link=rule.faq_link,
                file_pos=region_start + rel_pos,   # абсолютная позиция в файле
                file_match_len=match_len,
                notes=matching_notes, is_hidden=is_ignored,
            ))
    return findings