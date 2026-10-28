from __future__ import annotations

import re

from .custom_checks import CUSTOM_CHECKS
from .models import Finding, Note, Rule
from .normalization import (
    detect_log_type,
    extract_context,
    find_session_start,
    normalize_signature,
)


def _find_primary(lower: str, primary: str) -> int:
    primary_low = primary.lower()
    comma_idx = lower.rfind(primary_low + ",")
    if comma_idx >= 0:
        return comma_idx
    return lower.rfind(primary_low)


def _pick_block(matches: list[re.Match], rule: Rule) -> re.Match:
    all_of = [s.lower() for s in (rule.all_of or []) if s]
    any_of = [s.lower() for s in (rule.any_of or []) if s]
    if not all_of and not any_of:
        return matches[0]

    best = matches[0]
    best_score = (-1, -1)
    for match in matches:
        block_lower = match.group(0).lower()
        score = (
            sum(1 for s in all_of if s in block_lower),
            sum(1 for s in any_of if s in block_lower),
        )
        if score > best_score:
            best, best_score = match, score
    return best


def rule_matches(rule: Rule, lower: str, content: str):
    if rule.all_of and any(s.lower() not in lower for s in rule.all_of):
        return None
    if rule.any_of and not any(s.lower() in lower for s in rule.any_of):
        return None
    if rule.none_of and any(s.lower() in lower for s in rule.none_of):
        return None

    if rule.custom_check:
        check = CUSTOM_CHECKS.get(rule.custom_check)
        return check(content, lower, rule) if check else None

    if rule.block_pattern:
        try:
            matches = list(
                re.compile(rule.block_pattern, re.I | re.S).finditer(content)
            )
        except re.error:
            matches = []
        if matches:
            match = _pick_block(matches, rule)
            ctx = match.group(0)
            signature = ctx.split("\n", 1)[0][:200]
            return ctx, signature, match.start(), match.end() - match.start()

    primary = (rule.all_of or rule.any_of or [""])[0]
    if not primary:
        return None

    idx = _find_primary(lower, primary)
    if idx < 0:
        return None

    ctx = extract_context(content, idx, len(primary))
    end = content.find("\n", idx)
    if end < 0 or end - idx > 300:
        end = idx + 300
    return ctx, content[idx:end], idx, len(primary)


def pick_notes(notes: list[Note], rule_id: str, signature: str) -> list[Note]:
    return [n for n in notes if n.rule_id == rule_id and n.signature == signature]


def analyze(
    files: list[tuple[str, str]],
    rules: list[Rule],
    notes: list[Note],
) -> list[Finding]:
    findings: list[Finding] = []

    for file_name, content in files:
        log_type = detect_log_type(file_name)

        region_start = find_session_start(content)
        region = content[region_start:]
        lower = region.lower()

        for rule in rules:
            if not rule.enabled:
                continue
            if rule.log_type not in ("any", log_type):
                continue

            result = rule_matches(rule, lower, region)
            if not result:
                continue

            ctx, raw_signature, rel_pos, match_len = result
            signature = normalize_signature(raw_signature)
            matching_notes = pick_notes(notes, rule.id, signature)

            findings.append(
                Finding(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    category=rule.category,
                    file_name=file_name,
                    log_type=log_type,
                    context=ctx,
                    signature=signature,
                    explanation=rule.explanation,
                    suggestion=rule.suggestion,
                    faq_link=rule.faq_link,
                    file_pos=region_start + rel_pos,
                    file_match_len=match_len,
                    notes=matching_notes,
                    is_hidden=any(n.kind == "ignore" for n in matching_notes),
                    priority=rule.priority,
                )
            )

    return findings
