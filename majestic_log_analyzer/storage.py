from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

from .models import Rule, Note


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def bundled_data_dir() -> Path:
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        p = Path(meipass) / "data"
        if p.exists():
            return p
    for candidate in (app_dir() / "data", app_dir() / "_internal" / "data"):
        if candidate.exists():
            return candidate
    return app_dir() / "data"


def _can_write(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        test = path / ".write_test"
        test.write_text("", encoding="utf-8")
        test.unlink()
        return True
    except (PermissionError, OSError):
        return False


def _user_data_dir() -> Path:
    portable = app_dir() / "data"
    if _can_write(portable):
        return portable

    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if appdata:
            roaming = Path(appdata) / "MajesticLogAnalyzer" / "data"
            roaming.mkdir(parents=True, exist_ok=True)
            return roaming

    fallback = Path.home() / ".majestic_log_analyzer" / "data"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def _seed_user_data(user_dir: Path) -> None:
    src = bundled_data_dir()
    if not src.exists():
        return
    try:
        if src.resolve() == user_dir.resolve():
            return
    except OSError:
        pass

    user_dir.mkdir(parents=True, exist_ok=True)
    for name in ("rules.json", "notes.json", "exceptions.json", "ui.json", "settings.json"):
        s = src / name
        d = user_dir / name
        if s.exists() and not d.exists():
            try:
                shutil.copy2(s, d)
            except Exception as e:
                print(f"[storage] seed {name} failed: {e}")


APP_DIR = app_dir()
DATA_DIR = _user_data_dir()
_seed_user_data(DATA_DIR)

RULES_FILE = DATA_DIR / "rules.json"
NOTES_FILE = DATA_DIR / "notes.json"
EXCEPTIONS_FILE = DATA_DIR / "exceptions.json"
UI_FILE = DATA_DIR / "ui.json"
SETTINGS_FILE = DATA_DIR / "settings.json"


def bundled_rules_path() -> Path:
    return bundled_data_dir() / "rules.json"


def load_rules() -> list[Rule]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if RULES_FILE.exists():
        try:
            raw = json.loads(RULES_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, list) and raw:
                return [Rule.from_dict(r) for r in raw]
        except Exception as e:
            print(f"[storage] rules.json load failed: {e}")

    src = bundled_data_dir() / "rules.json"
    if src.exists():
        try:
            text = src.read_text(encoding="utf-8")
            RULES_FILE.write_text(text, encoding="utf-8")
            raw = json.loads(text)
            return [Rule.from_dict(r) for r in raw]
        except Exception as e:
            print(f"[storage] bundled rules load failed: {e}")
    return []


def save_rules(rules: list[Rule]) -> None:
    RULES_FILE.write_text(
        json.dumps([r.to_dict() for r in rules], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _read_note_file(path: Path) -> list[Note]:
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            return [Note.from_dict(n) for n in raw]
    except Exception as e:
        print(f"[storage] {path.name} load failed: {e}")
    return []


def load_notes() -> list[Note]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    notes: list[Note] = []
    exceptions: list[Note] = []
    seen: set[str] = set()

    def _add(n: Note) -> None:
        if n.id in seen:
            return
        seen.add(n.id)
        (exceptions if n.kind == "ignore" else notes).append(n)

    for n in _read_note_file(NOTES_FILE):
        _add(n)
    for n in _read_note_file(EXCEPTIONS_FILE):
        _add(n)

    if not notes and not exceptions:
        src = bundled_data_dir() / "notes.json"
        if src.exists():
            try:
                raw = json.loads(src.read_text(encoding="utf-8"))
                if isinstance(raw, list):
                    for n_dict in raw:
                        _add(Note.from_dict(n_dict))
                    NOTES_FILE.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception as e:
                print(f"[storage] bundled notes load failed: {e}")

    return notes + exceptions


def save_notes(notes: list[Note]) -> None:
    notes_only = [n for n in notes if n.kind != "ignore"]
    exceptions = [n for n in notes if n.kind == "ignore"]

    NOTES_FILE.write_text(
        json.dumps([n.to_dict() for n in notes_only], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    EXCEPTIONS_FILE.write_text(
        json.dumps([n.to_dict() for n in exceptions], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_ui() -> dict:
    if not UI_FILE.exists():
        src = bundled_data_dir() / "ui.json"
        if src.exists():
            try:
                UI_FILE.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception:
                pass
        if not UI_FILE.exists():
            try:
                UI_FILE.write_text("{}", encoding="utf-8")
            except Exception:
                pass
            return {}
    try:
        return json.loads(UI_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_ui(data: dict) -> None:
    UI_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_settings() -> dict:
    if not SETTINGS_FILE.exists():
        src = bundled_data_dir() / "settings.json"
        if src.exists():
            try:
                SETTINGS_FILE.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception:
                pass
        if not SETTINGS_FILE.exists():
            return {}
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_settings(data: dict) -> None:
    SETTINGS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )