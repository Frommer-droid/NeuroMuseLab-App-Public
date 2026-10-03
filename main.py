from __future__ import annotations

import ctypes
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.config.constants import APP_USER_MODEL_ID, LOGO_FILE_NAME, PROJECT_ROOT
from app.core.container import build_main_window
from app.ui.theme import apply_theme, enforce_button_proportions


def _set_windows_app_id() -> None:
    if sys.platform != "win32":
        return

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except (AttributeError, OSError):
        return


def main() -> int:
    _set_windows_app_id()
    app = QApplication(sys.argv)
    apply_theme(app)

    logo_path = PROJECT_ROOT / LOGO_FILE_NAME
    if logo_path.exists():
        app.setWindowIcon(QIcon(str(logo_path)))

    window = build_main_window()
    enforce_button_proportions(window)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
