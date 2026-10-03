from __future__ import annotations

from app.config.constants import (
    DATA_ROOT,
    LOG_DIRECTORY_NAME,
    LOG_FILE_NAME,
    SETTINGS_FILE_NAME,
)
from app.core.upload_manager import UploadManager
from app.services.session_logger import SessionLogger
from app.services.settings_service import SettingsService
from app.services.telegram_service import TelegramService
from app.ui.main_window import MainWindow


def build_main_window() -> MainWindow:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    settings_service = SettingsService(DATA_ROOT / SETTINGS_FILE_NAME)
    settings = settings_service.load()

    logger = SessionLogger(DATA_ROOT / LOG_DIRECTORY_NAME / LOG_FILE_NAME)
    telegram_service = TelegramService()
    upload_manager = UploadManager(
        telegram_service=telegram_service,
        logger=logger,
    )

    return MainWindow(
        settings=settings,
        settings_service=settings_service,
        logger=logger,
        upload_manager=upload_manager,
    )
