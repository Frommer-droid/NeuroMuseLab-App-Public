from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

from app.models.upload import UploadResult
from app.services.session_logger import SessionLogger
from app.services.telegram_service import TelegramService
from app.utils.text_utils import normalize_text

LogCallback = Callable[[str], None]


class UploadManager:
    def __init__(
        self,
        *,
        telegram_service: TelegramService,
        logger: SessionLogger,
    ) -> None:
        self._telegram_service = telegram_service
        self._logger = logger

    def verify_access(self, token: str, channel_id: str, on_log: LogCallback | None = None) -> str:
        self._validate_common(token, channel_id)
        bot_name = self._telegram_service.verify_access(token=token, channel_id=channel_id)
        self._emit_log(f"Подключение успешно. Бот: {bot_name}", on_log)
        return bot_name

    def publish_post(
        self,
        *,
        token: str,
        channel_id: str,
        donation_url: str,
        file_paths: Sequence[Path],
        cover_path: Path | None,
        poem_text: str,
        on_log: LogCallback | None = None,
    ) -> UploadResult:
        self._validate_common(token, channel_id)
        normalized_paths = self._normalize_audio_paths(file_paths)
        self._validate_audio_files(normalized_paths)
        self._validate_cover_file(cover_path)

        text = normalize_text(poem_text)
        self._emit_log(
            f"Старт публикации поста: {len(normalized_paths)} аудио ({', '.join(path.name for path in normalized_paths)})",
            on_log,
        )
        if cover_path:
            self._emit_log(f"Используем обложку: {cover_path.name}", on_log)
        else:
            self._emit_log("Обложка не выбрана. Публикуем только аудио.", on_log)
        result = self._telegram_service.send_audio_post(
            token=token,
            channel_id=channel_id,
            donation_url=donation_url,
            file_paths=normalized_paths,
            cover_path=cover_path,
            poem_text=text,
        )
        self._emit_log(
            f"Опубликовано: {len(normalized_paths)} аудио. "
            f"message_id={result.message_id}, доп. сообщений={result.extra_text_messages}",
            on_log,
        )
        return UploadResult(
            file_paths=tuple(normalized_paths),
            success=True,
            message_ids=result.message_ids,
            extra_text_messages=result.extra_text_messages,
        )

    def _emit_log(self, text: str, on_log: LogCallback | None, is_error: bool = False) -> None:
        line = self._logger.error(text) if is_error else self._logger.info(text)
        if on_log:
            on_log(line)

    @staticmethod
    def _validate_common(token: str, channel_id: str) -> None:
        if not token.strip():
            raise ValueError("Укажите токен бота.")
        if not channel_id.strip():
            raise ValueError("Укажите ID канала или @username канала.")

    @staticmethod
    def _normalize_audio_paths(file_paths: Sequence[Path]) -> list[Path]:
        return [Path(path) for path in file_paths]

    @staticmethod
    def _validate_audio_files(file_paths: Sequence[Path]) -> None:
        if not file_paths:
            raise ValueError("Выберите хотя бы один файл в формате .mp3")

        for file_path in file_paths:
            if not file_path.exists():
                raise ValueError(f"Файл не найден: {file_path}")
            if file_path.suffix.lower() != ".mp3":
                raise ValueError("Выберите файл в формате .mp3")

    @staticmethod
    def _validate_cover_file(file_path: Path | None) -> None:
        if file_path is None:
            return
        if not file_path.exists():
            raise ValueError(f"Обложка не найдена: {file_path}")
        if not file_path.is_file():
            raise ValueError(f"Неверный путь к обложке: {file_path}")
        if file_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise ValueError("Обложка должна быть в формате JPG, JPEG, PNG или WEBP.")
