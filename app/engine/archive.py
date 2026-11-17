"""High-level archive actions: list, extract and create.

This is the only module the UI calls. It builds 7-Zip command lines,
parses the results into ArchiveInfo / ArchiveEntry objects and keeps
all the format-specific details out of the interface code.
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Iterable, Optional

from .models import LEVELS, ArchiveEntry, ArchiveInfo, CreateOptions
from .sevenzip import CancelToken, ProgressFn, run_capture, run_pipeline, run_with_progress

# .tar files wrapped in another compressor need two 7-Zip passes.
COMPRESSED_TAR = (".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tbz",
                  ".tar.xz", ".txz", ".tar.zst", ".tzst")

# Files we treat as "open me" when dropped (everything else is "compress me").
ARCHIVE_EXTENSIONS = {
    ".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".tbz2", ".tbz",
    ".xz", ".txz", ".zst", ".tzst", ".cab", ".iso", ".001", ".r00", ".lzh",
    ".arj", ".wim", ".cpio", ".z", ".lzma",
}


def is_compressed_tar(path: Path) -> bool:
    return path.name.lower().endswith(COMPRESSED_TAR)


def looks_like_archive(path: Path) -> bool:
    return path.is_file() and (
        path.suffix.lower() in ARCHIVE_EXTENSIONS or is_compressed_tar(path)
    )


def _password_switch(password: str) -> str:
    # "-p" with nothing after it means "empty password": 7-Zip then fails
    # with a clear "Wrong password" error instead of asking on a console.
    return f"-p{password}"


# --------------------------------------------------------------------------
# Listing
# --------------------------------------------------------------------------
def list_archive(path: Path, password: str = "",
                 cancel: Optional[CancelToken] = None) -> ArchiveInfo:
    """Read the file list of an archive without extracting anything."""
    if is_compressed_tar(path):
        text = run_pipeline(
            ["x", "-so", "-bd", "-sccUTF-8", "-p", "--", str(path)],
            ["l", "-slt", "-si", "-ttar", "-sccUTF-8"],
            cancel=cancel,
        )
        _, entries = parse_slt(text)
        outer = path.name.lower().rsplit(".", 1)[-1]
        fmt = {"tgz": "gz", "tbz2": "bz2", "tbz": "bz2", "txz": "xz", "tzst": "zst"}.get(outer, outer)
        return ArchiveInfo(path=path, format=f"tar.{fmt}", entries=entries)

    text = run_capture(
        ["l", "-slt", "-sccUTF-8", _password_switch(password), "--", str(path)],
        password_given=bool(password), cancel=cancel,
    )
    fmt, entries = parse_slt(text)
    return ArchiveInfo(path=path, format=fmt, entries=entries)


def parse_slt(text: str) -> tuple[str, list[ArchiveEntry]]:
    """Parse the output of `7z l -slt` ("Key = Value" blocks)."""
    text = text.replace("\r\n", "\n")
    header, _, body = text.partition("\n----------\n")

    fmt = ""
    for line in header.splitlines():
        if line.startswith("Type = "):
            fmt = line[len("Type = "):].strip().lower()
    fmt = {"rar5": "rar", "gzip": "gz", "bzip2": "bz2"}.get(fmt, fmt)

    entries: list[ArchiveEntry] = []
    for block in body.split("\n\n"):
        props: dict[str, str] = {}
        for line in block.splitlines():
            key, sep, value = line.partition(" = ")
            if sep:
                props[key.strip()] = value
            elif line.endswith(" ="):  # empty value, e.g. "Created ="
                props[line[:-2].strip()] = ""
        path = props.get("Path", "").replace("\\", "/").strip("/")
        if not path:
            continue
        entries.append(ArchiveEntry(
            path=path,
            is_dir=props.get("Folder") == "+" or props.get("Attributes", "").startswith("D"),
            size=_to_int(props.get("Size")) or 0,
            packed_size=_to_int(props.get("Packed Size")),
            modified=props.get("Modified", "")[:16],
            encrypted=props.get("Encrypted") == "+",
        ))
    return fmt, entries


def _to_int(value: Optional[str]) -> Optional[int]:
    try:
        return int(value) if value else None
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Extracting
# --------------------------------------------------------------------------
def extract(path: Path, destination: Path, items: Optional[Iterable[str]] = None,
            password: str = "", progress: Optional[ProgressFn] = None,
            cancel: Optional[CancelToken] = None) -> Path:
    """Extract everything, or only `items` (paths inside the archive).

    Existing files are never overwritten: a clashing file gets a new
    name such as "photo_1.jpg" (7-Zip switch -aou).
    """
    destination.mkdir(parents=True, exist_ok=True)
    listfile = _write_listfile(items) if items else None
    selection = ["-scsUTF-8", f"-i@{listfile}"] if listfile else []
    try:
        if is_compressed_tar(path):
            run_pipeline(
                ["x", "-so", "-bsp2", "-sccUTF-8", "-p", "--", str(path)],
                ["x", "-si", "-ttar", f"-o{destination}", "-y", "-aou",
                 "-bso0", "-bsp0", "-sccUTF-8", *selection],
                progress=progress, cancel=cancel,
            )
        else:
            run_with_progress(
                ["x", f"-o{destination}", "-y", "-aou", "-bsp1", "-bso0", "-sccUTF-8",
                 _password_switch(password), *selection, "--", str(path)],
                password_given=bool(password), progress=progress, cancel=cancel,
            )
    finally:
        if listfile:
            os.unlink(listfile)
    if progress:
        progress(100, "")
    return destination


def _write_listfile(items: Iterable[str]) -> str:
    """Selected names go into a text file: safe for thousands of items."""
    fd, name = tempfile.mkstemp(prefix="qapshyq-", suffix=".txt")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        for item in items:
            handle.write(item.replace("/", os.sep) + "\n")
    return name


def default_extract_dir(path: Path) -> Path:
    """'photos.zip' -> 'photos/' next to it ('photos (2)/' if taken)."""
    name = path.name
    lower = name.lower()
    for ext in COMPRESSED_TAR + tuple(sorted(ARCHIVE_EXTENSIONS, key=len, reverse=True)):
        if lower.endswith(ext):
            name = name[: -len(ext)]
            break
    # "movie.part1.rar" -> "movie"
    name = re.sub(r"\.part\d+$", "", name, flags=re.IGNORECASE)
    base = path.parent / (name or "extracted")
    candidate, number = base, 2
    while candidate.exists() and any(candidate.iterdir()):
        candidate = base.with_name(f"{base.name} ({number})")
        number += 1
    return candidate


# --------------------------------------------------------------------------
# Creating
# --------------------------------------------------------------------------
def create(options: CreateOptions, progress: Optional[ProgressFn] = None,
           cancel: Optional[CancelToken] = None) -> Path:
    """Create a new .zip or .7z archive from files and folders.

    7-Zip writes to a temporary "*.part" file first. Only a finished,
    complete archive is renamed to the real name, so a cancelled or
    failed run never leaves a broken archive behind.
    """
    if options.format not in ("zip", "7z"):
        raise ValueError("Only ZIP and 7Z archives can be created.")
    output = options.output
    temp = output.with_name(output.name + ".part")
    temp.unlink(missing_ok=True)

    args = ["a", f"-t{options.format}", f"-mx{LEVELS[options.level]}",
            "-y", "-bsp1", "-bso0", "-sccUTF-8"]
    if options.password:
        args.append(f"-p{options.password}")
        if options.format == "zip":
            args.append("-mem=AES256")      # strong AES-256 instead of old ZipCrypto
        elif options.encrypt_names:
            args.append("-mhe=on")          # 7z: hide file names too
    args += ["--", str(temp), *[str(src) for src in options.sources]]

    try:
        run_with_progress(args, progress=progress, cancel=cancel)
        os.replace(temp, output)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise
    if progress:
        progress(100, "")
    return output
