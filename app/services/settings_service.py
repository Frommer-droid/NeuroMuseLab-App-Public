from __future__ import annotations

import json
from pathlib import Path

from app.models.settings import AppSettings


class SettingsService:
    def __init__(self, settings_path: Path) -> None:
        self._settings_path = settings_path

    def has_saved_settings(self) -> bool:
        return self._settings_path.exists()

    def load(self) -> AppSettings:
        if not self._settings_path.exists():
            return AppSettings()

        try:
            data = json.loads(self._settings_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return AppSettings()

        if not isinstance(data, dict):
            return AppSettings()

        return AppSettings.from_dict(data)

    def save(self, settings: AppSettings) -> None:
        self._settings_path.write_text(
            json.dumps(settings.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
