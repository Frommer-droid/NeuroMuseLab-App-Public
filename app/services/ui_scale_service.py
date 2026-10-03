from __future__ import annotations

from dataclasses import dataclass

BASE_LOGICAL_DPI = 96.0
REFERENCE_WIDTH = 2560
REFERENCE_HEIGHT = 1440

MIN_AUTO_UI_SCALE_PERCENT = 70
MAX_AUTO_UI_SCALE_PERCENT = 200
AUTO_UI_SCALE_STEP = 10

MIN_FINAL_UI_SCALE_PERCENT = 35
MAX_FINAL_UI_SCALE_PERCENT = 300
FINAL_UI_SCALE_STEP = 5

MIN_DELTA_UI_SCALE_PERCENT = -50
MAX_DELTA_UI_SCALE_PERCENT = 50
DELTA_UI_SCALE_STEP = 10

BASE_WINDOW_HEIGHT_PERCENT = 80
MIN_WINDOW_HEIGHT_PERCENT = 40
MAX_WINDOW_HEIGHT_PERCENT = 95


@dataclass(frozen=True)
class UIScaleComputation:
    auto_percent: int
    final_percent: int
    scale_factor: float


def clamp_int(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))


def round_to_step(value: float, step: int) -> int:
    if step <= 0:
        return round(value)
    return int(round(value / step) * step)


def normalize_delta_percent(delta_percent: int) -> int:
    rounded = round_to_step(float(delta_percent), DELTA_UI_SCALE_STEP)
    return clamp_int(rounded, MIN_DELTA_UI_SCALE_PERCENT, MAX_DELTA_UI_SCALE_PERCENT)


def calculate_auto_percent(width: int, height: int, logical_dpi: float) -> int:
    safe_width = max(1, int(width))
    safe_height = max(1, int(height))
    dpi = logical_dpi if logical_dpi > 0 else BASE_LOGICAL_DPI

    normalized_width = safe_width * (dpi / BASE_LOGICAL_DPI)
    normalized_height = safe_height * (dpi / BASE_LOGICAL_DPI)
    ratio = min(normalized_width / REFERENCE_WIDTH, normalized_height / REFERENCE_HEIGHT)
    raw_auto = ratio * 100.0

    rounded = round_to_step(raw_auto, AUTO_UI_SCALE_STEP)
    return clamp_int(rounded, MIN_AUTO_UI_SCALE_PERCENT, MAX_AUTO_UI_SCALE_PERCENT)


def calculate_final_percent(auto_percent: int, delta_percent: int) -> int:
    normalized_delta = normalize_delta_percent(delta_percent)
    raw_final = auto_percent + (auto_percent * normalized_delta / 100.0)
    rounded = round_to_step(raw_final, FINAL_UI_SCALE_STEP)
    return clamp_int(rounded, MIN_FINAL_UI_SCALE_PERCENT, MAX_FINAL_UI_SCALE_PERCENT)


def calculate_scale_factor(final_percent: int) -> float:
    normalized = clamp_int(final_percent, MIN_FINAL_UI_SCALE_PERCENT, MAX_FINAL_UI_SCALE_PERCENT)
    return normalized / 100.0


def calculate_window_height_percent(delta_percent: int) -> int:
    normalized_delta = normalize_delta_percent(delta_percent)
    raw_percent = BASE_WINDOW_HEIGHT_PERCENT * (1.0 + normalized_delta / 100.0)
    return clamp_int(round(raw_percent), MIN_WINDOW_HEIGHT_PERCENT, MAX_WINDOW_HEIGHT_PERCENT)


def calculate_target_window_height(available_height: int, minimum_height: int, delta_percent: int) -> int:
    safe_available_height = max(1, int(available_height))
    safe_minimum_height = max(1, int(minimum_height))
    lower_bound = min(safe_minimum_height, safe_available_height)

    height_percent = calculate_window_height_percent(delta_percent)
    raw_target = round(safe_available_height * height_percent / 100.0)
    return clamp_int(raw_target, lower_bound, safe_available_height)


def clamp_window_position(
    x: int,
    y: int,
    width: int,
    height: int,
    available_x: int,
    available_y: int,
    available_width: int,
    available_height: int,
) -> tuple[int, int]:
    max_x = available_x + max(0, available_width - width)
    max_y = available_y + max(0, available_height - height)
    clamped_x = clamp_int(x, available_x, max_x)
    clamped_y = clamp_int(y, available_y, max_y)
    return clamped_x, clamped_y


def compute_ui_scale(width: int, height: int, logical_dpi: float, delta_percent: int) -> UIScaleComputation:
    auto_percent = calculate_auto_percent(width=width, height=height, logical_dpi=logical_dpi)
    final_percent = calculate_final_percent(auto_percent=auto_percent, delta_percent=delta_percent)
    return UIScaleComputation(
        auto_percent=auto_percent,
        final_percent=final_percent,
        scale_factor=calculate_scale_factor(final_percent),
    )
