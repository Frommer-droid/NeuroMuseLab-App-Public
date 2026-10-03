"""Non-interactive frozen runtime probe for the release build."""

from __future__ import annotations

import httpx
import socksio
import telegram
from PySide6 import QtCore, QtGui, QtWidgets

from app.services import telegram_service
from app.ui import main_window, theme


def main() -> int:
    assert QtCore.QObject and QtGui.QIcon and QtWidgets.QApplication
    assert httpx.AsyncClient and socksio and telegram.Bot
    assert telegram_service.TelegramService and main_window.MainWindow and theme.THEME_COLORS
    print("FROZEN_IMPORT_OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
