from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from app.ui.audio_files_widget import AudioFilesWidget


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_audio_files_widget_adds_and_removes_rows(qt_app: QApplication) -> None:
    widget = AudioFilesWidget()

    assert widget.row_count() == 1

    widget.add_empty_row()
    widget.add_empty_row()

    assert widget.row_count() == 3

    widget.remove_row_at(1)

    assert widget.row_count() == 2


def test_audio_files_widget_clear_resets_to_single_empty_row(qt_app: QApplication) -> None:
    widget = AudioFilesWidget()
    widget.set_file_paths(["D:/Music/track_1.mp3", "D:/Music/track_2.mp3"])

    assert widget.file_paths() == ["D:/Music/track_1.mp3", "D:/Music/track_2.mp3"]

    widget.clear()

    assert widget.row_count() == 1
    assert widget.file_paths() == []


def test_audio_files_widget_keeps_all_rows_without_album_limit(qt_app: QApplication) -> None:
    widget = AudioFilesWidget()
    paths = [f"D:/Music/track_{index}.mp3" for index in range(12)]

    widget.set_file_paths(paths)

    assert widget.row_count() == 12
    assert widget.file_paths() == paths
