"""Plain data classes shared by the engine and the user interface."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ArchiveEntry:
    """One file or folder inside an archive."""

    path: str              # full path inside the archive, always using "/"
    is_dir: bool
    size: int              # uncompressed size in bytes
    packed_size: int | None
    modified: str          # "YYYY-MM-DD HH:MM" or "" if unknown
    encrypted: bool

    @property
    def name(self) -> str:
        return self.path.rsplit("/", 1)[-1]


@dataclass
class ArchiveInfo:
    """Everything the UI needs to show an opened archive."""

    path: Path
    format: str                         # "zip", "7z", "rar", "tar", "tar.gz", ...
    entries: list[ArchiveEntry] = field(default_factory=list)
    headers_encrypted: bool = False     # file list itself was password protected

    @property
    def files(self) -> list[ArchiveEntry]:
        return [e for e in self.entries if not e.is_dir]

    @property
    def total_size(self) -> int:
        return sum(e.size for e in self.files)

    @property
    def has_encrypted(self) -> bool:
        return self.headers_encrypted or any(e.encrypted for e in self.entries)


# Compression presets shown in the UI -> 7-Zip "-mx" level.
LEVELS = {"fast": 1, "normal": 5, "maximum": 9}


@dataclass
class CreateOptions:
    """Settings chosen in the "Create archive" dialog."""

    sources: list[Path]
    output: Path
    format: str = "zip"            # "zip" or "7z"
    level: str = "normal"          # key of LEVELS
    password: str = ""
    encrypt_names: bool = False    # 7z only: hide the file list too
