"""Friendly error types and translation of 7-Zip messages.

7-Zip prints technical messages such as
"ERROR: Cannot open encrypted archive. Wrong password?". The UI should
show something a normal person understands, so every failure is turned
into one of the exceptions below with a clear `message`.
"""
from __future__ import annotations


class ArchiveError(Exception):
    """Base class: `message` is safe to show to the user as-is."""

    def __init__(self, message: str, details: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.details = details  # raw 7-Zip output, for the "Details" button


class EngineMissing(ArchiveError):
    """The 7-Zip executable could not be found."""


class PasswordRequired(ArchiveError):
    """The archive (or its file list) is encrypted and needs a password."""


class WrongPassword(ArchiveError):
    """A password was given but it is not correct."""


class Cancelled(ArchiveError):
    """The user pressed Cancel."""


# (text that 7-Zip prints, message for the user) - checked in order.
_KNOWN_PROBLEMS: list[tuple[str, str]] = [
    ("dangerous link path", "Some items were skipped because they tried to write outside "
                            "the target folder. This archive may be unsafe."),
    ("cannot open the file as archive", "This file is not a supported archive, or it is damaged."),
    ("can not open the file as archive", "This file is not a supported archive, or it is damaged."),
    ("is not archive", "This file is not a supported archive, or it is damaged."),
    ("unexpected end of archive", "The archive is incomplete. It may not have finished downloading."),
    ("missing volume", "A part of this multi-part archive is missing. Put all parts in the same folder."),
    ("crc failed", "The archive is damaged: some files did not pass the integrity check."),
    ("data error", "The archive is damaged: some data could not be read."),
    ("headers error", "The archive is damaged: its file list could not be read."),
    ("unsupported method", "This archive uses a compression method that is not supported."),
    ("not enough space", "There is not enough free disk space."),
    ("no space left", "There is not enough free disk space."),
    ("access is denied", "Access denied. Choose another folder or close programs that use these files."),
    ("permission denied", "Access denied. Choose another folder or close programs that use these files."),
    ("cannot find the file", "A file could not be found. It may have been moved or deleted."),
    ("no such file", "A file could not be found. It may have been moved or deleted."),
    ("the system cannot find", "A file could not be found. It may have been moved or deleted."),
]


def translate(exit_code: int, output: str, password_given: bool) -> ArchiveError:
    """Turn a failed 7-Zip run into the most helpful ArchiveError."""
    text = output.lower()

    # Password problems are checked first: a wrong password often also
    # produces "Data Error", which would otherwise look like damage.
    if "wrong password" in text or "encrypted archive" in text:
        if password_given:
            return WrongPassword("The password is not correct. Please try again.", output)
        return PasswordRequired("This archive is protected with a password.", output)

    for needle, message in _KNOWN_PROBLEMS:
        if needle in text:
            return ArchiveError(message, output)

    if exit_code == 8:
        return ArchiveError("Not enough memory to finish this operation.", output)
    if exit_code == 255:
        return Cancelled("The operation was cancelled.", output)

    # Unknown problem: show the last meaningful line from 7-Zip.
    lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
    last = lines[-1] if lines else f"exit code {exit_code}"
    return ArchiveError(f"Something went wrong: {last}", output)
