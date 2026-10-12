from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Rule:
    id: str
    name: str
    log_type: str = "any"
    severity: str = "warning"
    category: str = ""
    enabled: bool = True
    all_of: list = field(default_factory=list)
    any_of: list = field(default_factory=list)
    none_of: list = field(default_factory=list)
    block_pattern: Optional[str] = None
    custom_check: Optional[str] = None
    count_pattern: str = ""
    count_expected: list = field(default_factory=list)
    explanation: str = ""
    suggestion: str = ""
    faq_link: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Rule":
        raw_expected = d.get("count_expected") or []
        expected: list[int] = []
        for x in raw_expected:
            try:
                expected.append(int(x))
            except (TypeError, ValueError):
                pass
        return cls(
            id=d["id"], name=d.get("name", d["id"]),
            log_type=d.get("log_type", "any"),
            severity=d.get("severity", "warning"),
            category=d.get("category", ""),
            enabled=bool(d.get("enabled", True)),
            all_of=list(d.get("all_of") or []),
            any_of=list(d.get("any_of") or []),
            none_of=list(d.get("none_of") or []),
            block_pattern=d.get("block_pattern"),
            custom_check=d.get("custom_check"),
            count_pattern=d.get("count_pattern") or "",
            count_expected=expected,
            explanation=d.get("explanation", ""),
            suggestion=d.get("suggestion", ""),
            faq_link=d.get("faq_link", ""),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name,
            "log_type": self.log_type, "severity": self.severity,
            "category": self.category, "enabled": self.enabled,
            "all_of": self.all_of, "any_of": self.any_of, "none_of": self.none_of,
            "block_pattern": self.block_pattern, "custom_check": self.custom_check,
            "count_pattern": self.count_pattern or None,
            "count_expected": self.count_expected,
            "explanation": self.explanation, "suggestion": self.suggestion,
            "faq_link": self.faq_link,
        }


@dataclass
@dataclass
class Note:
    id: str
    rule_id: str
    signature: str
    kind: str
    title: str = ""
    comment: str = ""
    preview: str = ""
    match_pattern: str = ""   # ← новое: regex для игнора "похожих"
    created_at: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Note":
        kind = d.get("kind", "note")
        if kind == "force":
            kind = "note"
        return cls(
            id=d.get("id") or "note-" + uuid.uuid4().hex[:10],
            rule_id=d["rule_id"],
            signature=d.get("signature", ""),
            kind=kind,
            title=d.get("title", ""),
            comment=d.get("comment", ""),
            preview=d.get("preview", ""),
            match_pattern=d.get("match_pattern", "") or "",
            created_at=d.get("created_at") or datetime.utcnow().isoformat() + "Z",
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id, "rule_id": self.rule_id,
            "signature": self.signature, "kind": self.kind,
            "title": self.title, "comment": self.comment,
            "preview": self.preview,
            "match_pattern": self.match_pattern,
            "created_at": self.created_at,
        }


@dataclass
class Finding:
    rule_id: str
    rule_name: str
    severity: str
    category: str
    file_name: str
    log_type: str
    context: str
    signature: str
    explanation: str
    suggestion: str
    faq_link: str
    file_pos: int = 0
    file_match_len: int = 0
    note: Optional[Note] = None
    is_hidden: bool = False


@dataclass
class LoadedFile:
    name: str
    content: str
    path: Optional[Path] = None
    from_discord: bool = False
    metadata: dict = field(default_factory=dict)