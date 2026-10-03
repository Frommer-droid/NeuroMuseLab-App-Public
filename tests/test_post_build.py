from __future__ import annotations

from pathlib import Path

from Build_Tools.post_build import finalize_build


def test_finalize_build_excludes_local_settings_and_logs(tmp_path: Path) -> None:
    dist_app = tmp_path / "Build_Tools" / "dist" / "NeuroMuseLab"
    dist_app.mkdir(parents=True)
    (dist_app / "NeuroMuseLab.exe").write_bytes(b"fixture")
    for name in ("logo.ico", "VERSION", "LICENSE"):
        (tmp_path / name).write_text(name, encoding="utf-8")
    (tmp_path / "settings.json").write_text("private", encoding="utf-8")
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "session.log").write_text("private", encoding="utf-8")

    portable = finalize_build(tmp_path)

    assert (portable / "NeuroMuseLab.exe").is_file()
    assert all((portable / name).is_file() for name in ("logo.ico", "VERSION", "LICENSE"))
    assert not (portable / "settings.json").exists()
    assert not (portable / "logs").exists()
    assert (tmp_path / "settings.json").read_text(encoding="utf-8") == "private"
