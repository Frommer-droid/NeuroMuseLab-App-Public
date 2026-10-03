from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import Lock


class SessionLogger:
    def __init__(self, log_path: Path) -> None:
        self._log_path = log_path
        self._records: list[str] = []
        self._lock = Lock()

        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_path.write_text("", encoding="utf-8")

    def info(self, message: str) -> str:
        return self._log("ИНФО", message)

    def warning(self, message: str) -> str:
        return self._log("ПРЕДУПР", message)

    def error(self, message: str) -> str:
        return self._log("ОШИБКА", message)

    def flush(self) -> None:
        with self._lock:
            body = "\n".join(self._records)
            if body:
                body += "\n"
            self._log_path.write_text(body, encoding="utf-8")

    def _log(self, level: str, message: str) -> str:
        timestamp = datetime.now(tz=timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] [{level}] {message}"
        with self._lock:
            self._records.append(line)
            with self._log_path.open("a", encoding="utf-8") as fp:
                fp.write(f"{line}\n")
        return line
