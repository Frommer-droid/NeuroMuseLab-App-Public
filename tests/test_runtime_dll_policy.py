from __future__ import annotations

from pathlib import Path

import pytest

from Build_Tools.runtime_dll_policy import (
    MSVC_RUNTIME_NAMES,
    prefer_pyside_msvc_runtime,
    validate_binary_origins,
)


def test_binary_origin_policy_rejects_foreign_runtime(tmp_path: Path) -> None:
    trusted = tmp_path / "trusted"
    foreign = tmp_path / "foreign"
    trusted.mkdir()
    foreign.mkdir()
    allowed = trusted / "allowed.dll"
    blocked = foreign / "blocked.dll"
    allowed.write_bytes(b"allowed")
    blocked.write_bytes(b"blocked")

    validate_binary_origins([("allowed.dll", str(allowed), "BINARY")], [trusted])
    with pytest.raises(RuntimeError, match="Untrusted native binary origins"):
        validate_binary_origins([("blocked.dll", str(blocked), "BINARY")], [trusted])


def test_root_runtime_uses_complete_pyside_set(tmp_path: Path) -> None:
    pyside_dir = tmp_path / "PySide6"
    pyside_dir.mkdir()
    for name in MSVC_RUNTIME_NAMES:
        (pyside_dir / name).write_bytes(b"qt")

    result = prefer_pyside_msvc_runtime(
        [("VCRUNTIME140.dll", "C:/Python/VCRUNTIME140.dll", "BINARY")], pyside_dir
    )

    assert {destination.casefold() for destination, _, _ in result} == set(MSVC_RUNTIME_NAMES)
    assert all(Path(source).parent == pyside_dir for _, source, _ in result)
