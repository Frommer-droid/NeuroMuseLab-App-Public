from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from functools import partial
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


@dataclass
class _AudioFileRow:
    container: QWidget
    line_edit: QLineEdit
    browse_button: QPushButton
    remove_button: QPushButton


class AudioFilesWidget(QWidget):
    files_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: list[_AudioFileRow] = []
        self._inputs_enabled = True

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(8)

        self._rows_layout = QVBoxLayout()
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(8)
        root_layout.addLayout(self._rows_layout)

        self.add_button = QPushButton("+ Добавить аудиофайл", self)
        self.add_button.setObjectName("standard_button")
        self.add_button.clicked.connect(self.add_empty_row)
        root_layout.addWidget(self.add_button, 0, Qt.AlignmentFlag.AlignLeft)

        self._append_row("", emit_change=False)
        self._sync_controls()

    def row_count(self) -> int:
        return len(self._rows)

    def file_paths(self) -> list[str]:
        return [row.line_edit.text().strip() for row in self._rows if row.line_edit.text().strip()]

    def set_file_paths(self, file_paths: Sequence[str]) -> None:
        normalized_paths = [str(path).strip() for path in file_paths if str(path).strip()]
        self._replace_rows(normalized_paths or [""], emit_change=True)

    def add_empty_row(self) -> None:
        self._append_row("", emit_change=True)
        self._sync_controls()

    def clear(self) -> None:
        self._replace_rows([""], emit_change=True)

    def remove_row_at(self, index: int) -> None:
        if not 0 <= index < len(self._rows):
            return
        if len(self._rows) == 1:
            self._rows[0].line_edit.clear()
            self.files_changed.emit()
            return

        row = self._rows.pop(index)
        row.container.deleteLater()
        self._sync_controls()
        self.files_changed.emit()

    def set_inputs_enabled(self, is_enabled: bool) -> None:
        self._inputs_enabled = is_enabled
        for row in self._rows:
            row.line_edit.setEnabled(is_enabled)
            row.browse_button.setEnabled(is_enabled)
            row.remove_button.setEnabled(is_enabled and len(self._rows) > 1)
        self.add_button.setEnabled(is_enabled)

    def _replace_rows(self, file_paths: Sequence[str], *, emit_change: bool) -> None:
        while self._rows:
            row = self._rows.pop()
            row.container.deleteLater()

        for path in file_paths:
            self._append_row(path, emit_change=False)

        self._sync_controls()
        if emit_change:
            self.files_changed.emit()

    def _append_row(self, file_path: str, *, emit_change: bool) -> None:
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        line_edit = QLineEdit(container)
        line_edit.setPlaceholderText("Выберите mp3-файл")
        line_edit.setText(file_path)
        line_edit.textChanged.connect(self.files_changed.emit)
        layout.addWidget(line_edit, 1)

        browse_button = QPushButton("Обзор", container)
        browse_button.setObjectName("standard_button")
        browse_button.clicked.connect(partial(self._choose_file, line_edit))
        layout.addWidget(browse_button)

        remove_button = QPushButton("×", container)
        remove_button.setObjectName("danger_btn")
        remove_button.clicked.connect(partial(self._remove_row, container))
        layout.addWidget(remove_button)

        self._rows_layout.addWidget(container)
        self._rows.append(
            _AudioFileRow(
                container=container,
                line_edit=line_edit,
                browse_button=browse_button,
                remove_button=remove_button,
            )
        )

        if emit_change:
            self.files_changed.emit()

    def _remove_row(self, container: QWidget) -> None:
        for index, row in enumerate(self._rows):
            if row.container is container:
                self.remove_row_at(index)
                return

    def _choose_file(self, line_edit: QLineEdit) -> None:
        current_text = line_edit.text().strip()
        start_dir = str(Path(current_text).parent) if current_text else ""
        file_name, _ = QFileDialog.getOpenFileName(self, "Выбор mp3-файла", start_dir, "MP3 (*.mp3)")
        if file_name:
            line_edit.setText(file_name)

    def _sync_controls(self) -> None:
        can_remove = len(self._rows) > 1
        for row in self._rows:
            row.remove_button.setVisible(can_remove)
            row.remove_button.setEnabled(self._inputs_enabled and can_remove)
        self.add_button.setEnabled(self._inputs_enabled)
