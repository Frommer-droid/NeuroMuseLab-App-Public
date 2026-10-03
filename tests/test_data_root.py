from pathlib import Path

import pytest

from app.config.constants import resolve_data_root


def test_portable_data_stays_with_executable(tmp_path: Path) -> None:
    assert resolve_data_root(tmp_path, "C:/Profiles/Example/AppData/Roaming") == tmp_path


def test_installed_data_is_per_user(tmp_path: Path) -> None:
    (tmp_path / "installed.marker").write_text("installed", encoding="utf-8")
    assert resolve_data_root(tmp_path, "C:/Profiles/Example/AppData/Roaming") == (
        Path("C:/Profiles/Example/AppData/Roaming") / "NeuroMuseLab"
    )


def test_installed_data_requires_appdata(tmp_path: Path) -> None:
    (tmp_path / "installed.marker").write_text("installed", encoding="utf-8")
    with pytest.raises(RuntimeError, match="APPDATA"):
        resolve_data_root(tmp_path, "")
