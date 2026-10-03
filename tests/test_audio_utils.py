from pathlib import Path

from app.utils.audio_utils import infer_performer_and_title


def test_infer_performer_and_title_from_dash_separator() -> None:
    performer, title = infer_performer_and_title(Path("Downloads/Лермонтов М. - Казачья колыбельная песня.mp3"))

    assert performer == "Лермонтов М."
    assert title == "Казачья колыбельная песня"


def test_infer_performer_and_title_from_initials_prefix_without_dash() -> None:
    performer, title = infer_performer_and_title(Path("Downloads/Лермонтов М. Есть речи - значенье.mp3"))

    assert performer == "Лермонтов М."
    assert title == "Есть речи - значенье"


def test_infer_performer_and_title_falls_back_to_folder_name() -> None:
    performer, title = infer_performer_and_title(Path("Лермонтов М./Казачья колыбельная песня.mp3"))

    assert performer == "Лермонтов М."
    assert title == "Казачья колыбельная песня"
