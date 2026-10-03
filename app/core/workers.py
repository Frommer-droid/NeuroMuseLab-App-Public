from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from app.core.upload_manager import UploadManager


class VerifyWorker(QThread):
    log_message = Signal(str)
    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, manager: UploadManager, token: str, channel_id: str) -> None:
        super().__init__()
        self._manager = manager
        self._token = token
        self._channel_id = channel_id

    def run(self) -> None:
        try:
            bot_name = self._manager.verify_access(
                token=self._token,
                channel_id=self._channel_id,
                on_log=self.log_message.emit,
            )
        except Exception as error:  # noqa: BLE001 - report unexpected worker errors through the UI signal
            self.failed.emit(str(error))
            return
        self.finished_ok.emit(bot_name)


class PostUploadWorker(QThread):
    log_message = Signal(str)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        manager: UploadManager,
        token: str,
        channel_id: str,
        donation_url: str,
        file_paths: list[Path],
        cover_path: Path | None,
        poem_text: str,
    ) -> None:
        super().__init__()
        self._manager = manager
        self._token = token
        self._channel_id = channel_id
        self._donation_url = donation_url
        self._file_paths = file_paths
        self._cover_path = cover_path
        self._poem_text = poem_text

    def run(self) -> None:
        try:
            result = self._manager.publish_post(
                token=self._token,
                channel_id=self._channel_id,
                donation_url=self._donation_url,
                file_paths=self._file_paths,
                cover_path=self._cover_path,
                poem_text=self._poem_text,
                on_log=self.log_message.emit,
            )
        except Exception as error:  # noqa: BLE001 - report unexpected worker errors through the UI signal
            self.failed.emit(str(error))
            return
        self.finished_ok.emit(result)
