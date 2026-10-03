"""GUI wrapper around the checked NeuroMuseLab portable build."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.ui.theme import apply_theme, enforce_button_proportions  # noqa: E402


class BuildThread(QThread):
    line_ready = Signal(str)
    build_finished = Signal(int)

    def run(self) -> None:
        command = [
            str(PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"),
            str(PROJECT_ROOT / "Build_Tools" / "build_release.py"),
        ]
        try:
            process = subprocess.Popen(
                command,
                cwd=PROJECT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            assert process.stdout is not None
            for line in process.stdout:
                self.line_ready.emit(line.rstrip())
            self.build_finished.emit(process.wait())
        except OSError as error:
            self.line_ready.emit(f"Не удалось запустить сборку: {error}")
            self.build_finished.emit(1)


class CompilerWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.thread: BuildThread | None = None
        self.setWindowTitle("Сборка NeuroMuseLab")
        self.setWindowIcon(QIcon(str(PROJECT_ROOT / "logo.ico")))
        self.resize(760, 500)

        root = QWidget(self)
        layout = QVBoxLayout(root)
        layout.addWidget(QLabel("Портативная сборка с проверкой DLL и frozen imports", root))
        self.log = QPlainTextEdit(root)
        self.log.setReadOnly(True)
        layout.addWidget(self.log, 1)
        buttons = QHBoxLayout()
        self.build_button = QPushButton("Собрать", root)
        self.build_button.setObjectName("primaryButton")
        self.build_button.clicked.connect(self.start_build)
        buttons.addWidget(self.build_button)
        self.clear_button = QPushButton("Очистить вывод", root)
        self.clear_button.clicked.connect(self.log.clear)
        buttons.addWidget(self.clear_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        self.setCentralWidget(root)
        enforce_button_proportions(self)

    def start_build(self) -> None:
        python = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
        if not python.is_file():
            QMessageBox.warning(self, "Нет окружения", "Создайте проектную .venv и установите зависимости.")
            return
        self.log.clear()
        self.build_button.setEnabled(False)
        self.thread = BuildThread(self)
        self.thread.line_ready.connect(self.log.appendPlainText)
        self.thread.build_finished.connect(self.finish_build)
        self.thread.start()

    def finish_build(self, exit_code: int) -> None:
        self.build_button.setEnabled(True)
        if exit_code == 0:
            self.log.appendPlainText("Проверенная портативная папка готова.")
        else:
            self.log.appendPlainText(f"Сборка остановлена. Код: {exit_code}")


def main() -> int:
    app = QApplication(sys.argv)
    apply_theme(app)
    window = CompilerWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
