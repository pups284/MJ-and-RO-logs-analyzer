from __future__ import annotations

import json
import re
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Optional


DISCORD_MSG_RE = re.compile(
    r"https?://(?:ptb\.|canary\.)?discord(?:app)?\.com/channels/"
    r"\d+/(?P<channel>\d+)/(?P<message>\d+)"
)

API_BASE   = "https://discord.com/api/v10"
USER_AGENT = "MajesticLogAnalyzer/2.2 (+https://majestic-rp.tech)"

TEMP_SUBDIR = "majestic-log-analyzer"


class DiscordError(Exception):
    pass


def parse_discord_url(url: str) -> tuple[str, str]:
    m = DISCORD_MSG_RE.search(url.strip())
    if not m:
        raise DiscordError(
            "Не удалось распознать ссылку. Ожидается "
            "https://discord.com/channels/<server>/<channel>/<message>"
        )
    return m.group("channel"), m.group("message")


def fetch_message(channel_id: str, message_id: str, token: str,
                  timeout: int = 15) -> dict:
    url = f"{API_BASE}/channels/{channel_id}/messages/{message_id}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bot {token}",
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise DiscordError("Неверный токен бота (401).")
        if e.code == 403:
            raise DiscordError(
                "Доступ запрещён (403). Убедитесь, что бот на сервере и имеет "
                "право «Read Message History» в этом канале."
            )
        if e.code == 404:
            raise DiscordError(
                "Сообщение или канал не найдены (404). Проверьте ссылку и "
                "что у бота есть доступ к каналу."
            )
        raise DiscordError(f"Discord API вернул ошибку {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise DiscordError(f"Не удалось связаться с Discord: {e.reason}")


def collect_attachments(message: dict) -> list[dict]:
    out: list[dict] = []
    for att in message.get("attachments", []) or []:
        out.append(att)
    ref = message.get("referenced_message")
    if isinstance(ref, dict):
        for att in ref.get("attachments", []) or []:
            out.append(att)
    return out


def is_log_like(filename: str) -> bool:
    n = (filename or "").lower()
    if n.endswith((".log", ".txt")):
        return True
    base = n.rsplit(".", 1)[0]
    for prefix in ("main", "client", "patcher", "cef", "service"):
        if base.startswith(prefix):
            return True
    return False


def discord_temp_dir() -> Path:
    d = Path(tempfile.gettempdir()) / TEMP_SUBDIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def download_attachment(att: dict, dest_dir: Path, timeout: int = 30) -> Path:
    filename = att.get("filename") or f"discord_{att.get('id', 'file')}"
    safe = re.sub(r"[^\w\-.]+", "_", filename)[:180] or "file"
    unique = f"discord_{att.get('id', 'x')}_{safe}"
    dest = dest_dir / unique
    req = urllib.request.Request(att["url"], headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        raise DiscordError(f"Не удалось скачать {filename}: HTTP {e.code}")
    except urllib.error.URLError as e:
        raise DiscordError(f"Не удалось скачать {filename}: {e.reason}")
    dest.write_bytes(data)
    return dest


def download_logs_from_url(
    url: str,
    token: str,
    *,
    allow_non_logs: bool = False,
    progress: Optional[Callable[[str], None]] = None,
) -> list[tuple[Path, str]]:
    """Скачивает вложения сообщения. Возвращает [(путь, оригинальное_имя), ...]."""
    channel_id, message_id = parse_discord_url(url)

    if progress:
        progress("Запрашиваю сообщение из Discord…")
    msg = fetch_message(channel_id, message_id, token)

    attachments = collect_attachments(msg)
    if not attachments:
        raise DiscordError("В сообщении (и в его reply) нет вложений.")

    selected = [
        a for a in attachments
        if allow_non_logs or is_log_like(a.get("filename", ""))
    ]
    if not selected:
        raise DiscordError(
            "Вложения есть, но ни одно не похоже на лог (.log/.txt/ main*/client*…). "
            "Поставьте галку «Скачивать любые вложения»."
        )

    dest_dir = discord_temp_dir()
    result: list[tuple[Path, str]] = []
    for i, att in enumerate(selected, 1):
        name = att.get("filename", "?")
        if progress:
            progress(f"Скачиваю {i}/{len(selected)}: {name}")
        path = download_attachment(att, dest_dir)
        result.append((path, name))
    return result


def cleanup_discord_files(paths: list[Optional[Path]]) -> int:
    """Удаляет файлы из temp, если они лежат в нашей temp-папке."""
    temp_root = discord_temp_dir().resolve()
    removed = 0
    for p in paths:
        if not p:
            continue
        try:
            rp = Path(p).resolve()
            if temp_root in rp.parents and rp.exists():
                rp.unlink()
                removed += 1
        except Exception:
            pass
    return removed