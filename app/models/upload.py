from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class UploadResult:
    file_paths: tuple[Path, ...]
    success: bool
    skipped: bool = False
    message_ids: tuple[int, ...] = ()
    extra_text_messages: int = 0
    error: str | None = None

    @property
    def audio_count(self) -> int:
        return len(self.file_paths)

    @property
    def message_id(self) -> int | None:
        return self.message_ids[0] if self.message_ids else None


@dataclass
class TelegramSendResult:
    message_ids: tuple[int, ...]
    extra_text_messages: int = 0

    @property
    def message_id(self) -> int | None:
        return self.message_ids[0] if self.message_ids else None
