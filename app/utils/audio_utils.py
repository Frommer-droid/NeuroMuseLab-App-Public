from __future__ import annotations

import re
from pathlib import Path


def collect_mp3_files(root_folder: Path) -> list[Path]:
    files = [path for path in root_folder.rglob("*.mp3") if path.is_file()]
    return sorted(files, key=lambda item: str(item).lower())


def _strip_performer_prefix(title: str, performer: str) -> str:
    title_value = title.strip()
    performer_value = performer.strip()
    if not title_value or not performer_value:
        return title_value

    performer_tokens = re.findall(r"[0-9A-Za-zА-Яа-яЁё]+", performer_value)
    if not performer_tokens:
        return title_value

    between = r"[\s\u00A0.\-—–:|,;_()\"'«»]*"
    after = r"[\s\u00A0.\-—–:|,;_()\"'«»]+"
    pattern = r"^\s*" + between.join(re.escape(token) for token in performer_tokens) + after

    match = re.match(pattern, title_value, flags=re.IGNORECASE)
    if not match:
        return title_value

    remainder = title_value[match.end() :]
    cleaned = remainder.lstrip(" \t\u00A0-—–:|.,;_()\"'«»")
    return cleaned or title_value


def _split_performer_and_title_from_stem(stem: str) -> tuple[str, str] | None:
    value = stem.strip()
    if not value:
        return None

    initials_match = re.match(
        r"^\s*([A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё'`-]+(?:\s+[A-Za-zА-Яа-яЁё]\.){1,2})\s+(.+?)\s*$",
        value,
    )
    if initials_match:
        performer, title_raw = initials_match.groups()
        title = title_raw.lstrip(" \t\u00A0-—–:|.,;_()\"'«»")
        if performer and title:
            return performer.strip(), title.strip()

    separator_match = re.match(r"^\s*(.+?)\s+[—–-]\s+(.+?)\s*$", value)
    if separator_match:
        performer, title = separator_match.groups()
        if performer and title:
            return performer.strip(), title.strip()

    return None


def infer_performer_and_title(file_path: Path) -> tuple[str | None, str]:
    raw_title = file_path.stem.strip() or file_path.name
    from_stem = _split_performer_and_title_from_stem(raw_title)
    if from_stem is not None:
        performer, title = from_stem
        return performer, title

    performer = file_path.parent.name.strip() if file_path.parent else ""
    title = _strip_performer_prefix(raw_title, performer)
    return performer or None, title
