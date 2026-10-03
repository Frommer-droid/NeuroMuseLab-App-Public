from __future__ import annotations

from pathlib import Path

import pytest

from app.core.upload_manager import UploadManager
from app.models.upload import TelegramSendResult


class _FakeLogger:
    def info(self, message: str) -> str:
        return message

    def error(self, message: str) -> str:
        return message


class _FakeTelegramService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def verify_access(self, token: str, channel_id: str) -> str:
        return "Bot"

    def send_audio_post(self, **kwargs) -> TelegramSendResult:
        self.calls.append(kwargs)
        file_paths = tuple(kwargs["file_paths"])
        return TelegramSendResult(message_ids=tuple(range(1, len(file_paths) + 1)))


def _build_manager() -> tuple[UploadManager, _FakeTelegramService]:
    telegram_service = _FakeTelegramService()
    manager = UploadManager(telegram_service=telegram_service, logger=_FakeLogger())
    return manager, telegram_service


def _create_audio_file(path: Path) -> Path:
    path.write_bytes(b"audio")
    return path


def test_publish_post_requires_at_least_one_audio_file(tmp_path: Path) -> None:
    manager, _telegram_service = _build_manager()

    with pytest.raises(ValueError, match="хотя бы один файл"):
        manager.publish_post(
            token="token",
            channel_id="@channel",
            donation_url="https://example.com/donate",
            file_paths=[],
            cover_path=None,
            poem_text="",
        )


def test_publish_post_rejects_missing_audio_file(tmp_path: Path) -> None:
    manager, _telegram_service = _build_manager()

    with pytest.raises(ValueError, match="Файл не найден"):
        manager.publish_post(
            token="token",
            channel_id="@channel",
            donation_url="https://example.com/donate",
            file_paths=[tmp_path / "missing.mp3"],
            cover_path=None,
            poem_text="",
        )


def test_publish_post_rejects_non_mp3_file(tmp_path: Path) -> None:
    manager, _telegram_service = _build_manager()
    invalid_file = tmp_path / "track.wav"
    invalid_file.write_bytes(b"audio")

    with pytest.raises(ValueError, match="формате .mp3"):
        manager.publish_post(
            token="token",
            channel_id="@channel",
            donation_url="https://example.com/donate",
            file_paths=[invalid_file],
            cover_path=None,
            poem_text="",
        )


def test_publish_post_passes_multiple_audio_files_to_telegram_service(tmp_path: Path) -> None:
    manager, telegram_service = _build_manager()
    audio_files = [
        _create_audio_file(tmp_path / "track_1.mp3"),
        _create_audio_file(tmp_path / "track_2.mp3"),
    ]

    result = manager.publish_post(
        token="token",
        channel_id="@channel",
        donation_url="https://example.com/donate",
        file_paths=audio_files,
        cover_path=None,
        poem_text="Текст",
    )

    assert len(telegram_service.calls) == 1
    assert tuple(telegram_service.calls[0]["file_paths"]) == tuple(audio_files)
    assert result.file_paths == tuple(audio_files)
    assert result.message_ids == (1, 2)


def test_publish_post_allows_more_than_ten_audio_files(tmp_path: Path) -> None:
    manager, telegram_service = _build_manager()
    audio_files = [_create_audio_file(tmp_path / f"track_{index}.mp3") for index in range(12)]

    result = manager.publish_post(
        token="token",
        channel_id="@channel",
        donation_url="https://example.com/donate",
        file_paths=audio_files,
        cover_path=None,
        poem_text="Общий текст",
    )

    assert len(telegram_service.calls) == 1
    assert tuple(telegram_service.calls[0]["file_paths"]) == tuple(audio_files)
    assert result.message_ids == tuple(range(1, 13))
