"""One Dark palette and scalable Qt widget styles."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication, QPushButton, QWidget

THEME_COLORS: dict[str, str] = {
    "background": "#282C34", "surface": "#21252B", "surface_alt": "#2C313C",
    "surface_hover": "#353B45", "surface_pressed": "#181A1F",
    "alternate": "#262A32", "selection": "#3E4451", "primary": "#3E4451",
    "primary_hover": "#4B5263", "accent": "#61AFEF",
    "accent_hover": "#7BC0F6", "accent_pressed": "#4D95C7",
    "success": "#98C379", "text": "#ABB2BF", "text_strong": "#E6E6E6",
    "muted": "#9DA5B4", "on_accent": "#21252B", "border": "#3E4451",
    "focus": "#61AFEF", "danger": "#E06C75", "danger_text": "#E8838B",
    "danger_surface": "#352A31", "warning": "#D19A66",
    "disabled_text": "#5C6370", "disabled_background": "#21252B",
    "disabled_border": "#2C313C", "scrollbar": "#4B5263",
}

DERIVED_COLORS: dict[str, str] = {"danger_pressed": "#A9505A"}


def _scaled(value: int, scale_factor: float, minimum: int = 1) -> int:
    return max(minimum, round(value * scale_factor))


def build_one_dark_stylesheet(scale_factor: float = 1.0) -> str:
    colors = {**THEME_COLORS, **DERIVED_COLORS}

    def px(value: int) -> int:
        return _scaled(value, scale_factor)

    return f"""
QWidget {{
    background: {colors['background']}; color: {colors['text']};
    font-family: "Tahoma", "Segoe UI", "Aptos", sans-serif;
    font-size: {px(10)}pt;
}}
QMainWindow {{ background: {colors['background']}; }}
QLabel {{ color: {colors['text']}; }}
QGroupBox {{
    background: {colors['surface']}; color: {colors['text_strong']};
    border: {px(1)}px solid {colors['border']};
    border-radius: {px(8)}px; margin-top: {px(16)}px; padding: {px(12)}px;
}}
QGroupBox::title {{
    subcontrol-origin: margin; subcontrol-position: top left;
    left: {px(12)}px; padding: 0 {px(6)}px;
    color: {colors['text_strong']}; font-weight: 700;
}}
QLineEdit, QPlainTextEdit, QTextEdit, QDoubleSpinBox, QComboBox {{
    background: {colors['surface_alt']}; color: {colors['text_strong']};
    border: {px(1)}px solid {colors['border']};
    border-radius: {px(6)}px; padding: {px(7)}px;
    selection-background-color: {colors['selection']};
    selection-color: {colors['text_strong']};
}}
QLineEdit:hover, QPlainTextEdit:hover, QTextEdit:hover, QComboBox:hover {{ border-color: {colors['primary_hover']}; }}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus {{ border-color: {colors['focus']}; }}
QLineEdit:disabled, QPlainTextEdit:disabled, QTextEdit:disabled, QComboBox:disabled {{
    background: {colors['disabled_background']}; color: {colors['disabled_text']};
    border-color: {colors['disabled_border']};
}}
QComboBox::drop-down {{ border: 0; width: {px(24)}px; }}
QComboBox QAbstractItemView {{
    background: {colors['surface']}; color: {colors['text_strong']};
    selection-background-color: {colors['selection']};
}}
QPushButton {{
    background: {colors['surface_hover']}; color: {colors['text_strong']};
    border: {px(1)}px solid {colors['border']};
    border-radius: {px(7)}px; padding: {px(7)}px {px(12)}px; font-weight: 600;
}}
QPushButton:hover {{ background: {colors['primary_hover']}; border-color: {colors['focus']}; }}
QPushButton:pressed, QPushButton:checked {{ background: {colors['surface_pressed']}; }}
QPushButton:focus {{ border: {px(2)}px solid {colors['focus']}; }}
QPushButton:disabled {{
    background: {colors['disabled_background']}; color: {colors['disabled_text']};
    border-color: {colors['disabled_border']};
}}
QPushButton#primaryButton {{
    background: {colors['accent']}; color: {colors['on_accent']};
    border-color: {colors['accent']};
}}
QPushButton#primaryButton:hover {{ background: {colors['accent_hover']}; }}
QPushButton#primaryButton:pressed, QPushButton#primaryButton:checked {{ background: {colors['accent_pressed']}; }}
QPushButton#danger_btn {{
    background: {colors['danger']}; color: {colors['on_accent']};
    border-color: {colors['danger']};
}}
QPushButton#danger_btn:hover {{ background: {colors['danger_text']}; }}
QPushButton#danger_btn:pressed, QPushButton#danger_btn:checked {{ background: {colors['danger_pressed']}; }}
QPushButton#primaryButton:disabled, QPushButton#danger_btn:disabled {{
    background: {colors['disabled_background']}; color: {colors['disabled_text']};
    border-color: {colors['disabled_border']};
}}
QProgressBar {{
    background: {colors['surface_alt']}; color: {colors['text_strong']};
    border: {px(1)}px solid {colors['border']};
    border-radius: {px(6)}px; text-align: center;
}}
QProgressBar::chunk {{ background: {colors['accent']}; border-radius: {px(5)}px; }}
QStatusBar {{ background: {colors['surface']}; color: {colors['text']}; }}
QStatusBar::item {{ border: none; }}
QScrollBar:vertical {{ background: {colors['surface']}; width: {px(10)}px; }}
QScrollBar::handle:vertical {{
    background: {colors['scrollbar']}; border-radius: {px(5)}px; min-height: {px(24)}px;
}}
QToolTip {{
    background: {colors['surface']}; color: {colors['text_strong']};
    border: {px(1)}px solid {colors['focus']};
}}
QComboBox#ui_scale_combo {{ min-width: {px(90)}px; }}
"""


def apply_theme(app: QApplication, scale_factor: float = 1.0) -> None:
    app.setStyleSheet(build_one_dark_stylesheet(scale_factor))


def enforce_button_proportions(root: QWidget) -> None:
    for button in root.findChildren(QPushButton):
        button.setMinimumWidth(max(button.minimumWidth(), button.sizeHint().height()))
