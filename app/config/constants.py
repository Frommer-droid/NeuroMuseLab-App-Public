from __future__ import annotations

import os
import sys
from pathlib import Path

APP_USER_MODEL_ID = "frommer.neuromuselab.telegram.audio.uploader.v1"

SETTINGS_FILE_NAME = "settings.json"
LOG_DIRECTORY_NAME = "logs"
LOG_FILE_NAME = "session.log"
LOGO_FILE_NAME = "logo.ico"

DEFAULT_WINDOW_X = 120
DEFAULT_WINDOW_Y = 120
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 860

MAX_AUDIO_CAPTION_LENGTH = 1024
MAX_TEXT_MESSAGE_LENGTH = 4096
SUPPORTED_AUDIO_EXTENSIONS = {".mp3"}

if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys.executable).resolve().parent
else:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_data_root(project_root: Path, appdata: str | None = None) -> Path:
    """Use per-user storage for installed copies and local files for source/portable copies."""
    if not (project_root / "installed.marker").is_file():
        return project_root
    roaming = appdata if appdata is not None else os.environ.get("APPDATA")
    if not roaming:
        raise RuntimeError("APPDATA is required for an installed NeuroMuseLab copy")
    return Path(roaming) / "NeuroMuseLab"


DATA_ROOT = resolve_data_root(PROJECT_ROOT)
