from __future__ import annotations

from app.services import ui_scale_service


def test_auto_percent_reference_resolution() -> None:
    assert ui_scale_service.calculate_auto_percent(2560, 1440, 96.0) == 100


def test_auto_percent_clamped_to_minimum() -> None:
    assert ui_scale_service.calculate_auto_percent(1600, 900, 96.0) == 70


def test_auto_percent_clamped_to_maximum() -> None:
    assert ui_scale_service.calculate_auto_percent(8000, 5000, 120.0) == 200


def test_final_percent_with_delta() -> None:
    assert ui_scale_service.calculate_final_percent(auto_percent=100, delta_percent=50) == 150
    assert ui_scale_service.calculate_final_percent(auto_percent=70, delta_percent=-50) == 35


def test_window_height_percent_formula() -> None:
    assert ui_scale_service.calculate_window_height_percent(0) == 80
    assert ui_scale_service.calculate_window_height_percent(50) == 95
    assert ui_scale_service.calculate_window_height_percent(-50) == 40


def test_target_window_height_with_clamp() -> None:
    assert ui_scale_service.calculate_target_window_height(available_height=1080, minimum_height=600, delta_percent=-50) == 600
    assert ui_scale_service.calculate_target_window_height(available_height=900, minimum_height=300, delta_percent=20) == 855


def test_compute_ui_scale_returns_final_factor() -> None:
    state = ui_scale_service.compute_ui_scale(width=2560, height=1440, logical_dpi=96.0, delta_percent=20)
    assert state.auto_percent == 100
    assert state.final_percent == 120
    assert state.scale_factor == 1.2
