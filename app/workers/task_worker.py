"""Runs one archive job in a background thread so the window never freezes."""
from __future__ import annotations

import time
import traceback
from typing import Any, Callable

from PySide6.QtCore import QThread, Signal

from app.engine.errors import ArchiveError
from app.engine.sevenzip import CancelToken, ProgressFn

# A job receives (progress callback, cancel token) and returns a result.
Job = Callable[[ProgressFn, CancelToken], Any]


class TaskWorker(QThread):
    progressed = Signal(int, str)   # percent, current file name
    succeeded = Signal(object)      # whatever the job returned
    failed = Signal(object)         # an ArchiveError

    def __init__(self, job: Job) -> None:
        super().__init__()
        self.job = job
        self.token = CancelToken()
        self._last_emit = 0.0
        self._last_percent = -1

    def run(self) -> None:          # runs in the background thread
        try:
            result = self.job(self._report, self.token)
        except ArchiveError as error:
            self.failed.emit(error)
        except Exception as error:  # a bug: still show a message, never crash
            self.failed.emit(ArchiveError(f"Unexpected error: {error}", traceback.format_exc()))
        else:
            self.succeeded.emit(result)

    def cancel(self) -> None:
        self.token.cancel()

    def _report(self, percent: int, name: str) -> None:
        # Send at most ~20 updates per second to keep the UI smooth.
        now = time.monotonic()
        if percent != self._last_percent or now - self._last_emit > 0.05:
            self._last_percent = percent
            self._last_emit = now
            self.progressed.emit(percent, name)
