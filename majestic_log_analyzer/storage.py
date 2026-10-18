from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

from .models import Rule, Note


# ─────────────────── пути ───────────────────

def app_dir() -> Path:
    """Папка, где лежит .exe (или корень проекта при запуске из исходников)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def bundled_data_dir() -> Path:
    """Папка data, вшитая в exe (read-only источник для первого запуска)."""
    # PyInstaller onedir: _MEIPASS указывает на _internal
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        p = Path(meipass) / "data"
        if p.exists():
            return p
    # Фолбэки для разных вариантов сборки / запуска из исходников
    for candidate in (
        app_dir() / "data",
        app_dir() / "_internal" / "data",
    ):
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
    """Куда писать в рантайме: рядом с exe (portable) или %APPDATA%."""
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
    """При первом запуске переносит файлы из bundled_data_dir в user_dir.
    Существующие файлы НЕ перезаписывает."""
    src = bundled_data_dir()
    if not src.exists():
        return
    try:
        if src.resolve() == user_dir.resolve():
            return
    except OSError:
        pass

    user_dir.mkdir(parents=True, exist_ok=True)
    for name in ("rules.json", "notes.json", "ui.json", "settings.json"):
        s = src / name
        d = user_dir / name
        if s.exists() and not d.exists():
            try:
                shutil.copy2(s, d)
                print(f"[storage] seeded {d} from {s}")
            except Exception as e:
                print(f"[storage] seed {name} failed: {e}")


# ─────────────────── глобальные пути ───────────────────

APP_DIR = app_dir()
DATA_DIR = _user_data_dir()
_seed_user_data(DATA_DIR)

RULES_FILE     = DATA_DIR / "rules.json"
NOTES_FILE     = DATA_DIR / "notes.json"
UI_FILE        = DATA_DIR / "ui.json"
SETTINGS_FILE  = DATA_DIR / "settings.json"


# Совместимость с rules_tab.reset_to_bundled() — теперь это data/rules.json
def bundled_rules_path() -> Path:
    return bundled_data_dir() / "rules.json"


# ─────────────────── rules ───────────────────

def load_rules() -> list[Rule]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if RULES_FILE.exists():
        try:
            raw = json.loads(RULES_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, list) and raw:
                return [Rule.from_dict(r) for r in raw]
        except Exception as e:
            print(f"[storage] rules.json load failed: {e}")
            print(f"[storage] file: {RULES_FILE}")

    # Файла нет / битый / пустой — пробуем восстановить из bundled data/
    src = bundled_data_dir() / "rules.json"
    if src.exists():
        try:
            text = src.read_text(encoding="utf-8")
            RULES_FILE.write_text(text, encoding="utf-8")
            raw = json.loads(text)
            print(f"[storage] restored rules.json from {src} ({len(raw)} rules)")
            return [Rule.from_dict(r) for r in raw]
        except Exception as e:
            print(f"[storage] bundled rules load failed: {e}")

    return []


def save_rules(rules: list[Rule]) -> None:
    RULES_FILE.write_text(
        json.dumps([r.to_dict() for r in rules], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ─────────────────── notes ───────────────────

def load_notes() -> list[Note]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if NOTES_FILE.exists():
        try:
            raw = json.loads(NOTES_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                return [Note.from_dict(n) for n in raw]
        except Exception as e:
            print(f"[storage] notes.json load failed: {e}")
            print(f"[storage] file: {NOTES_FILE}")

    src = bundled_data_dir() / "notes.json"
    if src.exists():
        try:
            text = src.read_text(encoding="utf-8")
            NOTES_FILE.write_text(text, encoding="utf-8")
            raw = json.loads(text)
            print(f"[storage] restored notes.json from {src} ({len(raw)} notes)")
            return [Note.from_dict(n) for n in raw]
        except Exception as e:
            print(f"[storage] bundled notes load failed: {e}")

    # ничего нет — создаём пустой файл, чтобы он был на месте
    try:
        NOTES_FILE.write_text("[]", encoding="utf-8")
    except Exception:
        pass
    return []


def save_notes(notes: list[Note]) -> None:
    NOTES_FILE.write_text(
        json.dumps([n.to_dict() for n in notes], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ─────────────────── ui ───────────────────

def load_ui() -> dict:
    if not UI_FILE.exists():
        # пробуем взять из bundled data/
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
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8",
    )


# ─────────────────── settings ───────────────────

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
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8",
    )