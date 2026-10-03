from __future__ import annotations

import sys
from pathlib import Path


def _read_version() -> str:
    if getattr(sys, "frozen", False):
        bundle_dir = getattr(sys, "_MEIPASS", None)
        candidates = []
        if bundle_dir:
            candidates.append(Path(bundle_dir) / "VERSION")
        candidates.append(Path(sys.executable).resolve().parent / "VERSION")
        for candidate in candidates:
            try:
                value = candidate.read_text(encoding="utf-8").strip()
            except (OSError, UnicodeError):
                continue
            if value:
                return value
        return "0.0.0"

    version_file = Path(__file__).resolve().parent.parent / "VERSION"
    if version_file.exists():
        value = version_file.read_text(encoding="utf-8").strip()
        if value:
            return value
    return "0.0.0"


__version__ = _read_version()
