from __future__ import annotations

import json
import sys
from pathlib import Path

from .models import Rule, Note


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def bundled_rules_path() -> Path:
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        p = Path(meipass) / "bundled_rules.json"
        if p.exists():
            return p
    return Path(__file__).resolve().parent.parent / "bundled_rules.json"


APP_DIR = app_dir()
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
RULES_FILE     = DATA_DIR / "rules.json"
NOTES_FILE     = DATA_DIR / "notes.json"
UI_FILE        = DATA_DIR / "ui.json"
SETTINGS_FILE  = DATA_DIR / "settings.json"


def load_rules() -> list[Rule]:
    if not RULES_FILE.exists():
        src = bundled_rules_path()
        if src.exists():
            RULES_FILE.write_text(src.read_text(encoding="utf-8"),
                                  encoding="utf-8")
    try:
        raw = json.loads(RULES_FILE.read_text(encoding="utf-8"))
        rules = [Rule.from_dict(r) for r in raw]
    except Exception as e:
        print("rules.json load failed:", e)
        return []

    # Одноразовая миграция: старое жёсткое [8, 31] у duplicate_count
    # превращаем в авто-режим (пустой список).
    migrated = False
    for r in rules:
        if r.custom_check == "duplicate_count" and r.count_expected == [8, 31]:
            r.count_expected = []
            migrated = True
    if migrated:
        try:
            save_rules(rules)
        except Exception as e:
            print("rules.json migration save failed:", e)

    return rules


def save_rules(rules: list[Rule]) -> None:
    RULES_FILE.write_text(
        json.dumps([r.to_dict() for r in rules], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_notes() -> list[Note]:
    if not NOTES_FILE.exists():
        return []
    try:
        raw = json.loads(NOTES_FILE.read_text(encoding="utf-8"))
        return [Note.from_dict(n) for n in raw]
    except Exception as e:
        print("notes.json load failed:", e)
        return []


def save_notes(notes: list[Note]) -> None:
    NOTES_FILE.write_text(
        json.dumps([n.to_dict() for n in notes], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_ui() -> dict:
    if not UI_FILE.exists():
        return {}
    try:
        return json.loads(UI_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_ui(data: dict) -> None:
    UI_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8",
    )


def load_settings() -> dict:
    if not SETTINGS_FILE.exists():
        return {}
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_settings(data: dict) -> None:
    SETTINGS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8",
    )