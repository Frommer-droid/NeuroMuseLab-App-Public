"""Fail-closed origin and MSVC runtime policy for PyInstaller builds."""

from __future__ import annotations

import os
import sys
from collections.abc import Iterable
from pathlib import Path

MSVC_RUNTIME_NAMES = (
    "concrt140.dll",
    "msvcp140.dll",
    "msvcp140_1.dll",
    "msvcp140_2.dll",
    "msvcp140_codecvt_ids.dll",
    "vcruntime140.dll",
    "vcruntime140_1.dll",
)

BinaryEntry = tuple[str, str, str]


def trusted_binary_roots(project_root: Path, extra_roots: Iterable[Path] = ()) -> tuple[Path, ...]:
    roots = (project_root, Path(sys.prefix), Path(sys.base_prefix))
    system_root = os.environ.get("SystemRoot")
    if system_root:
        roots += (Path(system_root),)
    return tuple(root.resolve() for root in (*roots, *extra_roots))


def validate_binary_origins(binaries: Iterable[BinaryEntry], trusted_roots: Iterable[Path]) -> None:
    roots = tuple(root.resolve() for root in trusted_roots)
    rejected = []
    for destination, source, _typecode in binaries:
        resolved = Path(source).resolve()
        if not any(resolved.is_relative_to(root) for root in roots):
            rejected.append((destination, str(resolved)))
    if rejected:
        details = "\n".join(f"{destination} <- {source}" for destination, source in rejected)
        raise RuntimeError(f"Untrusted native binary origins:\n{details}")


def prefer_pyside_msvc_runtime(binaries: Iterable[BinaryEntry], pyside_dir: Path) -> list[BinaryEntry]:
    """Replace only root runtime DLLs with one complete PySide6 set."""
    names = {name.casefold() for name in MSVC_RUNTIME_NAMES}
    result = [
        entry
        for entry in binaries
        if not (Path(entry[0]).parent == Path(".") and Path(entry[0]).name.casefold() in names)
    ]
    for name in MSVC_RUNTIME_NAMES:
        source = (pyside_dir / name).resolve()
        if not source.is_file():
            raise FileNotFoundError(f"PySide6 runtime DLL is missing: {source}")
        result.append((name, str(source), "BINARY"))
    return result
