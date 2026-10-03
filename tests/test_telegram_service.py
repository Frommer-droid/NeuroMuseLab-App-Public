from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Self

import pytest

try:
    import telegram  # type: ignore # noqa: F401
except ModuleNotFoundError:
    fake_telegram = types.ModuleType("telegram")
    fake_error = types.ModuleType("telegram.error")

    class TelegramError(Exception):
        pass

    class TimedOut(TelegramError):
        pass

    class Bot:
        pass

    class Message:
        pass

    class InlineKeyboardButton:
        def __init__(self, text: str, url: str) -> None:
            self.text = text
            self.url = url

    class InlineKeyboardMarkup:
        def __init__(self, inline_keyboard):
            self.inline_keyboard = inline_keyboard

    fake_error.TelegramError = TelegramError
    fake_error.TimedOut = TimedOut
    fake_telegram.Bot = Bot
    fake_telegram.Message = Message
    fake_telegram.InlineKeyboardButton = InlineKeyboardButton
    fake_telegram.InlineKeyboardMarkup = InlineKeyboardMarkup
    fake_telegram.error = fake_error

    sys.modules["telegram"] = fake_telegram
    sys.modules["telegram.error"] = fake_error

from app.services import telegram_service
from app.services.telegram_service import TelegramService, TelegramServiceError


class _FakeMessage:
    def __init__(self, message_id: int) -> None:
        self.message_id = message_id


class _FakeBot:
    def __init__(self, token: str) -> None:
        self.token = token
        self.calls: list[tuple[str, dict[str, object]]] = []
        self._message_id = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def send_photo(self, **kwargs):
        self._message_id += 1
        self.calls.append(("photo", kwargs))
        return _FakeMessage(self._message_id)

    async def send_audio(self, **kwargs):
        self._message_id += 1
        self.calls.append(("audio", kwargs))
        return _FakeMessage(self._message_id)

    async def send_message(self, **kwargs):
        self._message_id += 1
        self.calls.append(("text", kwargs))
        return _FakeMessage(self._message_id)


def _prepare_files(tmp_path: Path, with_cover: bool, audio_count: int = 1) -> tuple[list[Path], Path | None]:
    audio_files: list[Path] = []
    for index in range(audio_count):
        audio = tmp_path / f"track_{index + 1}.mp3"
        audio.write_bytes(b"audio")
        audio_files.append(audio)
    if not with_cover:
        return audio_files, None

    cover = tmp_path / "cover.jpg"
    cover.write_bytes(b"image")
    return audio_files, cover


def test_send_audio_post_with_cover_sends_photo_then_audio_then_text(monkeypatch, tmp_path: Path) -> None:
    fake_bot_holder: dict[str, _FakeBot] = {}

    def fake_bot_factory(token: str) -> _FakeBot:
        bot = _FakeBot(token)
        fake_bot_holder["bot"] = bot
        return bot

    monkeypatch.setattr(telegram_service.telegram, "Bot", fake_bot_factory)
    monkeypatch.setattr(telegram_service, "infer_performer_and_title", lambda _: ("Автор", "Трек"))

    audio_files, cover_file = _prepare_files(tmp_path, with_cover=True)
    poem = "а" * 4500

    service = TelegramService()
    result = service.send_audio_post(
        token="token",
        channel_id="@channel",
        donation_url="https://example.com/donate",
        file_paths=audio_files,
        cover_path=cover_file,
        poem_text=poem,
    )

    calls = fake_bot_holder["bot"].calls
    assert [kind for kind, _ in calls] == ["photo", "audio", "text", "text"]
    assert calls[0][1]["caption"] is None
    assert calls[0][1]["reply_markup"] is not None
    assert calls[1][1]["caption"] is None
    assert calls[1][1]["reply_markup"] is not None
    assert len(str(calls[2][1]["text"])) <= 4096
    assert len(str(calls[3][1]["text"])) <= 4096
    assert result.message_id == 2
    assert result.message_ids == (2,)
    assert result.extra_text_messages == 2


def test_send_audio_post_without_cover_puts_short_poem_into_audio_caption(monkeypatch, tmp_path: Path) -> None:
    fake_bot_holder: dict[str, _FakeBot] = {}

    def fake_bot_factory(token: str) -> _FakeBot:
        bot = _FakeBot(token)
        fake_bot_holder["bot"] = bot
        return bot

    monkeypatch.setattr(telegram_service.telegram, "Bot", fake_bot_factory)
    monkeypatch.setattr(telegram_service, "infer_performer_and_title", lambda _: ("Автор", "Трек"))

    audio_files, cover_file = _prepare_files(tmp_path, with_cover=False)
    poem = "Короткий текст"

    service = TelegramService()
    result = service.send_audio_post(
        token="token",
        channel_id="@channel",
        donation_url="https://example.com/donate",
        file_paths=audio_files,
        cover_path=cover_file,
        poem_text=poem,
    )

    calls = fake_bot_holder["bot"].calls
    assert [kind for kind, _ in calls] == ["audio"]
    assert calls[0][1]["caption"] == poem
    assert result.message_id == 1
    assert result.message_ids == (1,)
    assert result.extra_text_messages == 0


def test_send_audio_post_without_cover_sends_long_poem_as_text_messages(monkeypatch, tmp_path: Path) -> None:
    fake_bot_holder: dict[str, _FakeBot] = {}

    def fake_bot_factory(token: str) -> _FakeBot:
        bot = _FakeBot(token)
        fake_bot_holder["bot"] = bot
        return bot

    monkeypatch.setattr(telegram_service.telegram, "Bot", fake_bot_factory)
    monkeypatch.setattr(telegram_service, "infer_performer_and_title", lambda _: ("Автор", "Трек"))

    audio_files, cover_file = _prepare_files(tmp_path, with_cover=False)
    poem = "б" * 5000

    service = TelegramService()
    result = service.send_audio_post(
        token="token",
        channel_id="@channel",
        donation_url="https://example.com/donate",
        file_paths=audio_files,
        cover_path=cover_file,
        poem_text=poem,
    )

    calls = fake_bot_holder["bot"].calls
    assert [kind for kind, _ in calls] == ["audio", "text", "text"]
    assert calls[0][1]["caption"] is None
    assert len(str(calls[1][1]["text"])) <= 4096
    assert len(str(calls[2][1]["text"])) <= 4096
    assert result.message_id == 1
    assert result.message_ids == (1,)
    assert result.extra_text_messages == 2


def test_send_audio_post_multiple_files_sends_audio_messages_with_buttons(monkeypatch, tmp_path: Path) -> None:
    fake_bot_holder: dict[str, _FakeBot] = {}

    def fake_bot_factory(token: str) -> _FakeBot:
        bot = _FakeBot(token)
        fake_bot_holder["bot"] = bot
        return bot

    monkeypatch.setattr(telegram_service.telegram, "Bot", fake_bot_factory)
    monkeypatch.setattr(
        telegram_service,
        "infer_performer_and_title",
        lambda path: ("Автор", path.stem),
    )

    audio_files, _cover_file = _prepare_files(tmp_path, with_cover=False, audio_count=2)
    poem = "Общий текст публикации"
    donation_url = "https://example.com/donate"

    service = TelegramService()
    result = service.send_audio_post(
        token="token",
        channel_id="@channel",
        donation_url=donation_url,
        file_paths=audio_files,
        cover_path=None,
        poem_text=poem,
    )

    calls = fake_bot_holder["bot"].calls
    assert [kind for kind, _ in calls] == ["audio", "audio", "text"]
    assert calls[0][1]["caption"] is None
    assert calls[1][1]["caption"] is None
    assert calls[0][1]["reply_markup"] is not None
    assert calls[1][1]["reply_markup"] is not None
    assert calls[2][1]["text"] == poem
    assert result.message_id == 1
    assert result.message_ids == (1, 2)
    assert result.extra_text_messages == 1


def test_send_audio_post_multiple_files_with_cover_sends_cover_once_with_donation_button_then_audio_messages(
    monkeypatch, tmp_path: Path
) -> None:
    fake_bot_holder: dict[str, _FakeBot] = {}

    def fake_bot_factory(token: str) -> _FakeBot:
        bot = _FakeBot(token)
        fake_bot_holder["bot"] = bot
        return bot

    monkeypatch.setattr(telegram_service.telegram, "Bot", fake_bot_factory)
    monkeypatch.setattr(telegram_service, "infer_performer_and_title", lambda path: ("Автор", path.stem))

    audio_files, cover_file = _prepare_files(tmp_path, with_cover=True, audio_count=3)

    service = TelegramService()
    result = service.send_audio_post(
        token="token",
        channel_id="@channel",
        donation_url="https://example.com/donate",
        file_paths=audio_files,
        cover_path=cover_file,
        poem_text="Короткий текст",
    )

    calls = fake_bot_holder["bot"].calls
    assert [kind for kind, _ in calls] == ["photo", "audio", "audio", "audio", "text"]
    assert calls[0][1]["reply_markup"] is not None
    assert calls[1][1]["reply_markup"] is not None
    assert calls[2][1]["reply_markup"] is not None
    assert calls[3][1]["reply_markup"] is not None
    assert result.message_id == 2
    assert result.message_ids == (2, 3, 4)


def test_send_audio_post_multiple_files_sends_long_poem_after_last_audio(monkeypatch, tmp_path: Path) -> None:
    fake_bot_holder: dict[str, _FakeBot] = {}

    def fake_bot_factory(token: str) -> _FakeBot:
        bot = _FakeBot(token)
        fake_bot_holder["bot"] = bot
        return bot

    monkeypatch.setattr(telegram_service.telegram, "Bot", fake_bot_factory)
    monkeypatch.setattr(telegram_service, "infer_performer_and_title", lambda path: ("Автор", path.stem))

    audio_files, _cover_file = _prepare_files(tmp_path, with_cover=False, audio_count=2)
    poem = "б" * 5000

    service = TelegramService()
    result = service.send_audio_post(
        token="token",
        channel_id="@channel",
        donation_url="https://example.com/donate",
        file_paths=audio_files,
        cover_path=None,
        poem_text=poem,
    )

    calls = fake_bot_holder["bot"].calls
    assert [kind for kind, _ in calls] == ["audio", "audio", "text", "text"]
    assert calls[0][1]["caption"] is None
    assert calls[1][1]["caption"] is None
    assert len(str(calls[2][1]["text"])) <= 4096
    assert len(str(calls[3][1]["text"])) <= 4096
    assert result.message_id == 1
    assert result.message_ids == (1, 2)
    assert result.extra_text_messages == 2


def test_empty_donation_url_sends_no_button_on_cover_or_audio(monkeypatch, tmp_path: Path) -> None:
    fake_bot_holder: dict[str, _FakeBot] = {}

    def fake_bot_factory(token: str) -> _FakeBot:
        bot = _FakeBot(token)
        fake_bot_holder["bot"] = bot
        return bot

    monkeypatch.setattr(telegram_service.telegram, "Bot", fake_bot_factory)
    monkeypatch.setattr(telegram_service, "infer_performer_and_title", lambda path: ("Автор", path.stem))
    audio_files, cover_file = _prepare_files(tmp_path, with_cover=True, audio_count=2)

    TelegramService().send_audio_post(
        token="token",
        channel_id="@channel",
        donation_url="",
        file_paths=audio_files,
        cover_path=cover_file,
        poem_text="",
    )

    calls = fake_bot_holder["bot"].calls
    assert [kind for kind, _ in calls] == ["photo", "audio", "audio"]
    assert all(payload["reply_markup"] is None for _, payload in calls)


def test_send_audio_post_multiple_files_stops_on_second_audio_error(monkeypatch, tmp_path: Path) -> None:
    class _FailingBot(_FakeBot):
        async def send_audio(self, **kwargs):
            self._message_id += 1
            self.calls.append(("audio", kwargs))
            if self._message_id == 2:
                raise telegram_service.TelegramError("network failed")
            return _FakeMessage(self._message_id)

    fake_bot_holder: dict[str, _FailingBot] = {}

    def fake_bot_factory(token: str) -> _FailingBot:
        bot = _FailingBot(token)
        fake_bot_holder["bot"] = bot
        return bot

    monkeypatch.setattr(telegram_service.telegram, "Bot", fake_bot_factory)
    monkeypatch.setattr(telegram_service, "infer_performer_and_title", lambda path: ("Автор", path.stem))

    audio_files, _cover_file = _prepare_files(tmp_path, with_cover=False, audio_count=3)

    service = TelegramService()
    with pytest.raises(TelegramServiceError, match="Не удалось отправить пост"):
        service.send_audio_post(
            token="token",
            channel_id="@channel",
            donation_url="https://example.com/donate",
            file_paths=audio_files,
            cover_path=None,
            poem_text="Общий текст",
        )

    calls = fake_bot_holder["bot"].calls
    assert [kind for kind, _ in calls] == ["audio", "audio"]
