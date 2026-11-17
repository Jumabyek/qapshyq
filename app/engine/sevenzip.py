"""Find the 7-Zip program and run it with live progress and cancel.

We never implement compression ourselves. The real work is done by
7-Zip (7z.exe on Windows, 7zz on macOS/Linux): a fast, proven,
open-source engine. Everything runs locally; nothing is uploaded.
"""
from __future__ import annotations

import codecs
import os
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import IO, Callable, Optional

from .errors import Cancelled, EngineMissing, translate

# Folder of the project, or of the unpacked app after PyInstaller packaging.
if getattr(sys, "frozen", False):
    BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
else:
    BASE_DIR = Path(__file__).resolve().parents[2]

IS_WINDOWS = sys.platform.startswith("win")
# Hide the black console window that would flash on Windows.
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# progress(percent 0-100, current file name or "")
ProgressFn = Callable[[int, str], None]

# Matches 7-Zip progress text such as " 42% 12 + photos/cat.jpg".
_PERCENT = re.compile(r"(\d{1,3})%(?:\s+\d+)?(?:\s+[-+=U]\s+(.+))?")
# 7-Zip redraws its progress line with backspaces and carriage returns.
_SEPARATORS = re.compile(r"[\x08\r\n]+")


# --------------------------------------------------------------------------
# Locating the engine
# --------------------------------------------------------------------------
def find_7z() -> Optional[Path]:
    """Return the path to 7-Zip, preferring the copy bundled in ./bin."""
    names = ["7z.exe"] if IS_WINDOWS else ["7zz", "7z"]
    candidates = [BASE_DIR / "bin" / name for name in names]
    # Developers can point to any 7-Zip build with an environment variable.
    override = os.environ.get("QAPSHYQ_7Z")
    if override:
        candidates.insert(0, Path(override))
    if IS_WINDOWS:
        for env in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"):
            root = os.environ.get(env)
            if root:
                candidates.append(Path(root) / "7-Zip" / "7z.exe")
    else:
        # Homebrew locations on Apple Silicon and Intel Macs.
        candidates += [Path("/opt/homebrew/bin/7zz"), Path("/usr/local/bin/7zz")]

    for path in candidates:
        if path.is_file():
            return path
    for name in ("7zz", "7z"):
        found = shutil.which(name)
        if found:
            return Path(found)
    return None


def require_7z() -> Path:
    exe = find_7z()
    if exe is None:
        raise EngineMissing(
            "The 7-Zip engine was not found. Run the setup script again "
            "or put 7z.exe and 7z.dll (Windows) / 7zz (macOS) into the 'bin' folder."
        )
    return exe


def engine_version() -> str:
    """Short version text such as '7-Zip 26.06', or a hint if missing."""
    exe = find_7z()
    if exe is None:
        return "7-Zip engine not found"
    result = subprocess.run(
        [str(exe)], capture_output=True, stdin=subprocess.DEVNULL, creationflags=NO_WINDOW
    )
    banner = result.stdout.decode("utf-8", "replace")
    match = re.search(r"7-Zip[^\d]*(\d+\.\d+)", banner)
    return f"7-Zip {match.group(1)}" if match else "7-Zip"


# --------------------------------------------------------------------------
# Cancelling
# --------------------------------------------------------------------------
class CancelToken:
    """Shared between the UI (which cancels) and the running job.

    Cancelling kills the 7-Zip process immediately, so even a huge file
    stops at once instead of waiting for the next progress update.
    """

    def __init__(self) -> None:
        self._cancelled = False
        self._processes: list[subprocess.Popen] = []
        self._lock = threading.Lock()

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    def cancel(self) -> None:
        with self._lock:
            self._cancelled = True
            for proc in self._processes:
                _kill(proc)

    def attach(self, proc: subprocess.Popen) -> None:
        with self._lock:
            self._processes.append(proc)
            if self._cancelled:
                _kill(proc)

    def detach(self, proc: subprocess.Popen) -> None:
        with self._lock:
            if proc in self._processes:
                self._processes.remove(proc)


def _kill(proc: subprocess.Popen) -> None:
    try:
        proc.kill()
    except OSError:
        pass  # already finished


# --------------------------------------------------------------------------
# Running 7-Zip
# --------------------------------------------------------------------------
def _spawn(args: list[str], stdin=subprocess.DEVNULL) -> subprocess.Popen:
    # stdin is never the keyboard: 7-Zip must not wait for typed input.
    return subprocess.Popen(
        [str(require_7z()), *args],
        stdin=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=NO_WINDOW,
    )


def _drain(stream: IO[bytes], sink: list[bytes]) -> threading.Thread:
    """Read a whole pipe in the background (prevents pipe deadlocks)."""
    thread = threading.Thread(target=lambda: sink.append(stream.read()), daemon=True)
    thread.start()
    return thread


def _read_progress(stream: IO[bytes], progress: Optional[ProgressFn]) -> str:
    """Read 7-Zip progress output, call `progress`, return all text."""
    decoder = codecs.getincrementaldecoder("utf-8")("replace")
    collected: list[str] = []
    pending = ""
    last: tuple[int, str] = (-1, "")
    while True:
        chunk = stream.read1(4096) if hasattr(stream, "read1") else stream.read(4096)
        if not chunk:
            break
        text = decoder.decode(chunk)
        collected.append(text)
        pending += text
        pieces = _SEPARATORS.split(pending)
        pending = pieces.pop()  # last piece may be unfinished
        for piece in pieces:
            match = _PERCENT.search(piece)
            if match and progress:
                current = (min(int(match.group(1)), 100), (match.group(2) or "").strip())
                if current != last:
                    last = current
                    progress(*current)
    return "".join(collected)


def _close_pipes(*procs: subprocess.Popen) -> None:
    for proc in procs:
        for stream in (proc.stdout, proc.stderr):
            if stream and not stream.closed:
                stream.close()


def _finish(proc: subprocess.Popen, output: str, cancel: Optional[CancelToken],
            password_given: bool) -> None:
    """Raise the right error if 7-Zip failed or was cancelled."""
    if cancel is not None:
        cancel.detach(proc)
        if cancel.cancelled:
            raise Cancelled("The operation was cancelled.")
    # 0 = OK, 1 = finished with warnings (e.g. one file was locked).
    if proc.returncode not in (0, 1):
        raise translate(proc.returncode, output, password_given)


def run_capture(args: list[str], *, password_given: bool = False,
                cancel: Optional[CancelToken] = None) -> str:
    """Run 7-Zip and return its normal output (used for listing)."""
    proc = _spawn(args)
    if cancel:
        cancel.attach(proc)
    out, err = proc.communicate()
    output = out.decode("utf-8", "replace").replace("\r\n", "\n")
    _finish(proc, output + "\n" + err.decode("utf-8", "replace"), cancel, password_given)
    return output


def run_with_progress(args: list[str], *, password_given: bool = False,
                      progress: Optional[ProgressFn] = None,
                      cancel: Optional[CancelToken] = None) -> str:
    """Run 7-Zip with `-bsp1` (progress on stdout) and report it live."""
    proc = _spawn(args)
    if cancel:
        cancel.attach(proc)
    errors: list[bytes] = []
    err_thread = _drain(proc.stderr, errors)
    text = _read_progress(proc.stdout, progress)
    proc.wait()
    err_thread.join()
    _close_pipes(proc)
    output = text + "\n" + b"".join(errors).decode("utf-8", "replace")
    _finish(proc, output, cancel, password_given)
    return output


def run_pipeline(first: list[str], second: list[str], *,
                 progress: Optional[ProgressFn] = None,
                 cancel: Optional[CancelToken] = None) -> str:
    """Run `7z first | 7z second` (used for .tar.gz and friends).

    The first process unpacks the outer .gz/.xz/.bz2 layer to a stream,
    the second one reads the .tar inside it. Progress comes from the first
    process (it must use -bsp2). Returns the second process's output.
    """
    p1 = _spawn(first)
    p2 = _spawn(second, stdin=p1.stdout)
    assert p1.stdout is not None
    p1.stdout.close()  # p2 owns this pipe now
    if cancel:
        cancel.attach(p1)
        cancel.attach(p2)

    out2: list[bytes] = []
    err2: list[bytes] = []
    threads = [_drain(p2.stdout, out2), _drain(p2.stderr, err2)]
    text1 = _read_progress(p1.stderr, progress)
    p1.wait()
    p2.wait()
    for thread in threads:
        thread.join()
    _close_pipes(p1, p2)

    output2 = b"".join(out2).decode("utf-8", "replace").replace("\r\n", "\n")
    errors = text1 + "\n" + b"".join(err2).decode("utf-8", "replace")
    _finish(p1, errors, cancel, False)
    _finish(p2, output2 + "\n" + errors, cancel, False)
    return output2
