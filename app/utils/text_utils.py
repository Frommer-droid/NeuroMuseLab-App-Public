from __future__ import annotations

from app.config.constants import MAX_TEXT_MESSAGE_LENGTH


def normalize_text(value: str) -> str:
    return value.replace("\r\n", "\n").strip()


def split_text_for_telegram(text: str, max_length: int = MAX_TEXT_MESSAGE_LENGTH) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []
    if len(text) <= max_length:
        return [text]

    chunks: list[str] = []
    current = ""

    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip("\n")
        if not paragraph:
            continue

        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) <= max_length:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(paragraph) <= max_length:
            current = paragraph
            continue

        start = 0
        while start < len(paragraph):
            chunks.append(paragraph[start : start + max_length])
            start += max_length

    if current:
        chunks.append(current)

    return chunks
