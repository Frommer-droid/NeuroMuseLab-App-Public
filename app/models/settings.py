from __future__ import annotations

from dataclasses import dataclass, field

from app.config import constants
from app.services import ui_scale_service


def _to_int(value: object, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_scale_mode(value: object) -> str:
    mode = str(value or "auto").strip().lower()
    if mode != "auto":
        return "auto"
    return mode


def _to_audio_files(data: dict[str, object]) -> list[str]:
    raw_files = data.get("audio_files")
    if isinstance(raw_files, list):
        values = [str(item).strip() for item in raw_files if str(item).strip()]
        if values:
            return values

    legacy_file = str(data.get("single_file", "") or "").strip()
    return [legacy_file] if legacy_file else []


@dataclass
class WindowSettings:
    x: int = constants.DEFAULT_WINDOW_X
    y: int = constants.DEFAULT_WINDOW_Y
    width: int = constants.DEFAULT_WINDOW_WIDTH
    height: int = constants.DEFAULT_WINDOW_HEIGHT
    maximized: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, object] | None) -> WindowSettings:
        data = data or {}
        return cls(
            x=_to_int(data.get("x"), constants.DEFAULT_WINDOW_X),
            y=_to_int(data.get("y"), constants.DEFAULT_WINDOW_Y),
            width=_to_int(data.get("width"), constants.DEFAULT_WINDOW_WIDTH),
            height=_to_int(data.get("height"), constants.DEFAULT_WINDOW_HEIGHT),
            maximized=bool(data.get("maximized", False)),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "maximized": self.maximized,
        }


@dataclass
class AppSettings:
    bot_token: str = ""
    channel_id: str = ""
    donation_url: str = ""
    audio_files: list[str] = field(default_factory=list)
    single_file: str = ""
    single_cover_file: str = ""
    poem_text: str = ""
    ui_scale_mode: str = "auto"
    ui_scale_delta_percent: int = 0
    ui_scale_percent: int = 100
    window: WindowSettings = field(default_factory=WindowSettings)

    @classmethod
    def from_dict(cls, data: dict[str, object] | None) -> AppSettings:
        data = data or {}
        raw_delta = data.get("ui_scale_delta_percent")
        raw_percent = data.get("ui_scale_percent")

        if raw_delta is None and raw_percent is not None:
            legacy_delta = _to_int(raw_percent, 100) - 100
            delta_percent = ui_scale_service.normalize_delta_percent(legacy_delta)
        else:
            delta_percent = ui_scale_service.normalize_delta_percent(_to_int(raw_delta, 0))

        ui_scale_percent = _to_int(raw_percent, 100)
        ui_scale_percent = ui_scale_service.clamp_int(
            ui_scale_percent,
            ui_scale_service.MIN_FINAL_UI_SCALE_PERCENT,
            ui_scale_service.MAX_FINAL_UI_SCALE_PERCENT,
        )

        return cls(
            bot_token=str(data.get("bot_token", "") or ""),
            channel_id=str(data.get("channel_id", "") or ""),
            donation_url=str(data.get("donation_url", "") or ""),
            audio_files=_to_audio_files(data),
            single_file=str(data.get("single_file", "") or ""),
            single_cover_file=str(data.get("single_cover_file", "") or ""),
            poem_text=str(data.get("poem_text", "") or ""),
            ui_scale_mode=_to_scale_mode(data.get("ui_scale_mode")),
            ui_scale_delta_percent=delta_percent,
            ui_scale_percent=ui_scale_percent,
            window=WindowSettings.from_dict(data.get("window") if isinstance(data, dict) else None),
        )

    def to_dict(self) -> dict[str, object]:
        audio_files = [path.strip() for path in self.audio_files if path.strip()]
        return {
            "bot_token": self.bot_token,
            "channel_id": self.channel_id,
            "donation_url": self.donation_url,
            "audio_files": audio_files,
            "single_file": audio_files[0] if audio_files else "",
            "single_cover_file": self.single_cover_file,
            "poem_text": self.poem_text,
            "ui_scale_mode": _to_scale_mode(self.ui_scale_mode),
            "ui_scale_delta_percent": ui_scale_service.normalize_delta_percent(self.ui_scale_delta_percent),
            "ui_scale_percent": ui_scale_service.clamp_int(
                int(self.ui_scale_percent),
                ui_scale_service.MIN_FINAL_UI_SCALE_PERCENT,
                ui_scale_service.MAX_FINAL_UI_SCALE_PERCENT,
            ),
            "window": self.window.to_dict(),
        }
