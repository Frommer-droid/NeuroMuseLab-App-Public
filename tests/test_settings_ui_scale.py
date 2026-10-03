from __future__ import annotations

from app.models.settings import AppSettings


def test_ui_scale_migrates_legacy_percent_to_delta() -> None:
    settings = AppSettings.from_dict({"ui_scale_percent": 130})
    assert settings.ui_scale_mode == "auto"
    assert settings.ui_scale_delta_percent == 30
    assert settings.ui_scale_percent == 130


def test_ui_scale_delta_has_priority_over_legacy_percent() -> None:
    settings = AppSettings.from_dict({"ui_scale_delta_percent": 20, "ui_scale_percent": 150})
    assert settings.ui_scale_delta_percent == 20
    assert settings.ui_scale_percent == 150


def test_ui_scale_is_normalized_when_saving() -> None:
    settings = AppSettings(
        ui_scale_mode="manual",
        ui_scale_delta_percent=27,
        ui_scale_percent=999,
    )
    payload = settings.to_dict()
    assert payload["ui_scale_mode"] == "auto"
    assert payload["ui_scale_delta_percent"] == 30
    assert payload["ui_scale_percent"] == 300


def test_audio_files_migrate_from_legacy_single_file() -> None:
    settings = AppSettings.from_dict({"single_file": "D:/Music/track.mp3"})

    assert settings.audio_files == ["D:/Music/track.mp3"]


def test_audio_files_are_saved_and_update_legacy_single_file() -> None:
    settings = AppSettings(
        audio_files=["D:/Music/track_1.mp3", "D:/Music/track_2.mp3"],
        single_file="устаревшее-значение.mp3",
    )

    payload = settings.to_dict()

    assert payload["audio_files"] == ["D:/Music/track_1.mp3", "D:/Music/track_2.mp3"]
    assert payload["single_file"] == "D:/Music/track_1.mp3"


def test_donation_url_is_empty_by_default_and_preserved_when_saved() -> None:
    assert AppSettings().donation_url == ""
    assert AppSettings.from_dict({}).donation_url == ""
    assert AppSettings.from_dict({"donation_url": ""}).donation_url == ""
    assert AppSettings.from_dict({"donation_url": "https://example.com/donate"}).to_dict()["donation_url"] == (
        "https://example.com/donate"
    )
