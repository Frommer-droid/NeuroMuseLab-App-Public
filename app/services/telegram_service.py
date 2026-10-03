from __future__ import annotations

import asyncio
from collections.abc import Sequence
from pathlib import Path

import telegram
from telegram.error import TelegramError, TimedOut

from app.config.constants import MAX_AUDIO_CAPTION_LENGTH
from app.models.upload import TelegramSendResult
from app.utils.audio_utils import infer_performer_and_title
from app.utils.text_utils import normalize_text, split_text_for_telegram


class TelegramServiceError(RuntimeError):
    pass


REQUEST_READ_TIMEOUT = 120
REQUEST_WRITE_TIMEOUT = 120
REQUEST_CONNECT_TIMEOUT = 20
REQUEST_POOL_TIMEOUT = 60
MAX_RETRY_ATTEMPTS = 2
RETRY_DELAY_SECONDS = 1.5


class TelegramService:
    def verify_access(self, token: str, channel_id: str) -> str:
        return asyncio.run(self._verify_access_async(token, channel_id))

    def send_audio_post(
        self,
        *,
        token: str,
        channel_id: str,
        donation_url: str,
        file_paths: Sequence[Path],
        cover_path: Path | None,
        poem_text: str,
    ) -> TelegramSendResult:
        return asyncio.run(
            self._send_audio_post_async(
                token=token,
                channel_id=channel_id,
                donation_url=donation_url,
                file_paths=file_paths,
                cover_path=cover_path,
                poem_text=poem_text,
            )
        )

    async def _verify_access_async(self, token: str, channel_id: str) -> str:
        try:
            bot = telegram.Bot(token=token)
            async with bot:
                me = await bot.get_me()
                await bot.get_chat(chat_id=channel_id)
            return me.full_name
        except TelegramError as error:
            raise TelegramServiceError(f"Telegram API вернул ошибку: {error}") from error

    async def _send_audio_post_async(
        self,
        *,
        token: str,
        channel_id: str,
        donation_url: str,
        file_paths: Sequence[Path],
        cover_path: Path | None,
        poem_text: str,
    ) -> TelegramSendResult:
        normalized_paths = tuple(Path(path) for path in file_paths)
        if not normalized_paths:
            raise TelegramServiceError("Не переданы аудиофайлы для публикации.")
        for file_path in normalized_paths:
            if not file_path.exists():
                raise TelegramServiceError(f"Файл не найден: {file_path}")
        if cover_path is not None and not cover_path.exists():
            raise TelegramServiceError(f"Обложка не найдена: {cover_path}")

        poem = normalize_text(poem_text)
        donation_markup = self._build_donation_markup(donation_url)
        is_multi_audio = len(normalized_paths) > 1

        try:
            bot = telegram.Bot(token=token)
            async with bot:
                extra_messages = 0
                if cover_path is not None:
                    await self._send_cover_with_retry(
                        bot=bot,
                        channel_id=channel_id,
                        cover_path=cover_path,
                        caption=None,
                        reply_markup=donation_markup,
                    )

                separate_text = ""
                if is_multi_audio:
                    messages = await self._send_audio_messages_with_retry(
                        bot=bot,
                        channel_id=channel_id,
                        file_paths=normalized_paths,
                        reply_markup=donation_markup,
                    )
                    message_ids = tuple(message.message_id for message in messages)
                    separate_text = poem
                else:
                    performer, title = infer_performer_and_title(normalized_paths[0])
                    audio_caption = poem if cover_path is None and poem and len(poem) <= MAX_AUDIO_CAPTION_LENGTH else None
                    if poem and audio_caption is None:
                        separate_text = poem

                    message = await self._send_audio_with_retry(
                        bot=bot,
                        channel_id=channel_id,
                        file_path=normalized_paths[0],
                        performer=performer,
                        title=title,
                        caption=audio_caption,
                        reply_markup=donation_markup,
                    )
                    message_ids = (message.message_id,)

                if separate_text:
                    for chunk in split_text_for_telegram(separate_text):
                        await bot.send_message(chat_id=channel_id, text=chunk)
                        extra_messages += 1

                return TelegramSendResult(message_ids=message_ids, extra_text_messages=extra_messages)
        except TelegramError as error:
            raise TelegramServiceError(f"Не удалось отправить пост: {error}") from error

    async def _send_cover_with_retry(
        self,
        *,
        bot: telegram.Bot,
        channel_id: str,
        cover_path: Path,
        caption: str | None,
        reply_markup: telegram.InlineKeyboardMarkup | None,
    ) -> None:
        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            try:
                with cover_path.open("rb") as cover_file:
                    await bot.send_photo(
                        chat_id=channel_id,
                        photo=cover_file,
                        caption=caption,
                        reply_markup=reply_markup,
                        read_timeout=REQUEST_READ_TIMEOUT,
                        write_timeout=REQUEST_WRITE_TIMEOUT,
                        connect_timeout=REQUEST_CONNECT_TIMEOUT,
                        pool_timeout=REQUEST_POOL_TIMEOUT,
                    )
                return
            except TimedOut as error:
                if attempt < MAX_RETRY_ATTEMPTS:
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
                    continue
                raise TelegramServiceError(
                    "Тайм-аут сети при отправке обложки. Проверьте интернет/VPN и повторите попытку."
                ) from error

    async def _send_audio_with_retry(
        self,
        *,
        bot: telegram.Bot,
        channel_id: str,
        file_path: Path,
        performer: str | None,
        title: str,
        caption: str | None,
        reply_markup: telegram.InlineKeyboardMarkup | None,
    ) -> telegram.Message:
        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            try:
                with file_path.open("rb") as audio_file:
                    return await bot.send_audio(
                        chat_id=channel_id,
                        audio=audio_file,
                        performer=performer,
                        title=title,
                        caption=caption,
                        reply_markup=reply_markup,
                        read_timeout=REQUEST_READ_TIMEOUT,
                        write_timeout=REQUEST_WRITE_TIMEOUT,
                        connect_timeout=REQUEST_CONNECT_TIMEOUT,
                        pool_timeout=REQUEST_POOL_TIMEOUT,
                    )
            except TimedOut as error:
                if attempt < MAX_RETRY_ATTEMPTS:
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
                    continue
                raise TelegramServiceError(
                    "Тайм-аут сети при отправке аудио. Проверьте интернет/VPN и повторите попытку."
                ) from error

    async def _send_audio_messages_with_retry(
        self,
        *,
        bot: telegram.Bot,
        channel_id: str,
        file_paths: Sequence[Path],
        reply_markup: telegram.InlineKeyboardMarkup | None,
    ) -> tuple[telegram.Message, ...]:
        messages: list[telegram.Message] = []
        for file_path in file_paths:
            performer, title = infer_performer_and_title(file_path)
            message = await self._send_audio_with_retry(
                bot=bot,
                channel_id=channel_id,
                file_path=file_path,
                performer=performer,
                title=title,
                caption=None,
                reply_markup=reply_markup,
            )
            messages.append(message)
        return tuple(messages)

    @staticmethod
    def _normalize_donation_url(donation_url: str) -> str:
        return (donation_url or "").strip()

    @classmethod
    def _build_donation_markup(cls, donation_url: str) -> telegram.InlineKeyboardMarkup | None:
        url = cls._normalize_donation_url(donation_url)
        if not url:
            return None
        return telegram.InlineKeyboardMarkup(
            [[telegram.InlineKeyboardButton(text="Поддержать автора донатом", url=url)]]
        )
