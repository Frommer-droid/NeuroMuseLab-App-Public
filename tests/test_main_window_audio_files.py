from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from app.models.settings import AppSettings
from app.ui.main_window import MainWindow


class _FakeLogger:
    def info(self, message: str) -> str:
        return message

    def error(self, message: str) -> str:
        return message

    def flush(self) -> None:
        return None


class _FakeSettingsService:
    def __init__(self) -> None:
        self.saved_settings: AppSettings | None = None

    def has_saved_settings(self) -> bool:
        return False

    def save(self, settings: AppSettings) -> None:
        self.saved_settings = settings


class _FakeUploadManager:
    def verify_access(self, *args, **kwargs) -> str:
        return "Bot"

    def publish_post(self, *args, **kwargs):
        raise RuntimeError("not used in UI test")


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_window_restores_multiple_audio_files_from_settings(qt_app: QApplication) -> None:
    settings = AppSettings(
        audio_files=["D:/Music/track_1.mp3", "D:/Music/track_2.mp3"],
        single_cover_file="D:/Covers/cover.jpg",
        poem_text="Текст",
    )
    settings_service = _FakeSettingsService()
    window = MainWindow(
        settings=settings,
        settings_service=settings_service,
        logger=_FakeLogger(),
        upload_manager=_FakeUploadManager(),
    )

    try:
        assert window.audio_files_widget.file_paths() == ["D:/Music/track_1.mp3", "D:/Music/track_2.mp3"]
        assert window.single_cover_edit.text() == "D:/Covers/cover.jpg"
        assert window.poem_text_edit.toPlainText() == "Текст"
    finally:
        window.close()


def test_main_window_saves_multiple_audio_files_to_settings(qt_app: QApplication) -> None:
    settings = AppSettings()
    settings_service = _FakeSettingsService()
    window = MainWindow(
        settings=settings,
        settings_service=settings_service,
        logger=_FakeLogger(),
        upload_manager=_FakeUploadManager(),
    )

    try:
        window.audio_files_widget.set_file_paths(["D:/Music/one.mp3", "D:/Music/two.mp3"])
        window.single_cover_edit.setText("D:/Covers/cover.jpg")
        window.poem_text_edit.setPlainText("Общий текст")

        window._save_ui_to_settings()

        assert window._settings.audio_files == ["D:/Music/one.mp3", "D:/Music/two.mp3"]
        assert window._settings.single_file == "D:/Music/one.mp3"
        assert window._settings.single_cover_file == "D:/Covers/cover.jpg"
        assert window._settings.poem_text == "Общий текст"
    finally:
        window.close()


def test_main_window_shows_multi_audio_hint_for_separate_messages(qt_app: QApplication) -> None:
    settings = AppSettings()
    settings_service = _FakeSettingsService()
    window = MainWindow(
        settings=settings,
        settings_service=settings_service,
        logger=_FakeLogger(),
        upload_manager=_FakeUploadManager(),
    )

    try:
        window.audio_files_widget.set_file_paths(["D:/Music/one.mp3", "D:/Music/two.mp3"])
        window.poem_text_edit.setPlainText("Общий текст")
        window._update_poem_hint()

        assert "отдельным сообщением" in window.poem_hint_label.text()
    finally:
        window.close()
