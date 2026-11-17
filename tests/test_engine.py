"""Automated tests for the archive engine.

Run from the project folder:   python -m unittest discover -s tests -v
They need the 7-Zip engine (bin/7z.exe, bin/7zz, or QAPSHYQ_7Z=path).
"""
from __future__ import annotations

import os
import sys
import tarfile
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.engine import archive  # noqa: E402
from app.engine.errors import ArchiveError, Cancelled, PasswordRequired, WrongPassword  # noqa: E402
from app.engine.models import CreateOptions  # noqa: E402
from app.engine.sevenzip import CancelToken, find_7z  # noqa: E402

DATA = Path(__file__).parent / "data"


@unittest.skipIf(find_7z() is None, "7-Zip engine not available")
class EngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.src = self.tmp / "My Files"
        (self.src / "sub" / "deep").mkdir(parents=True)
        (self.src / "a.txt").write_text("hello", encoding="utf-8")
        (self.src / "sub" / "b.txt").write_text("world", encoding="utf-8")
        (self.src / "sub" / "deep" / "c.txt").write_text("deep", encoding="utf-8")
        (self.src / "Сәлем әлем.txt").write_text("қазақша", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def make(self, fmt="zip", level="normal", password="", encrypt_names=False) -> Path:
        out = self.tmp / f"test.{fmt}"
        progress: list[int] = []
        archive.create(CreateOptions([self.src], out, fmt, level, password, encrypt_names),
                       progress=lambda p, _n: progress.append(p))
        self.assertTrue(out.is_file())
        self.assertFalse(out.with_name(out.name + ".part").exists())
        self.assertEqual(progress[-1], 100)
        return out

    def paths(self, info) -> set[str]:
        return {e.path for e in info.files}

    # --- create + list ------------------------------------------------------
    def test_zip_and_7z_all_levels(self) -> None:
        for fmt in ("zip", "7z"):
            for level in ("fast", "normal", "maximum"):
                with self.subTest(fmt=fmt, level=level):
                    info = archive.list_archive(self.make(fmt, level))
                    self.assertEqual(info.format, fmt)
                    self.assertIn("My Files/Сәлем әлем.txt", self.paths(info))
                    self.assertEqual(len(info.files), 4)
                    self.assertEqual(info.total_size, len("hello") * 2 + len("deep")
                                     + len("қазақша".encode()))

    def test_extract_all_and_selected(self) -> None:
        arc = self.make("7z")
        out = archive.extract(arc, self.tmp / "out")
        self.assertEqual((out / "My Files" / "sub" / "deep" / "c.txt").read_text(), "deep")

        sel = archive.extract(arc, self.tmp / "sel", items=["My Files/sub", "My Files/a.txt"])
        self.assertTrue((sel / "My Files" / "sub" / "deep" / "c.txt").is_file())
        self.assertTrue((sel / "My Files" / "a.txt").is_file())
        self.assertFalse((sel / "My Files" / "Сәлем әлем.txt").exists())

    def test_extract_never_overwrites(self) -> None:
        arc = self.make("zip")
        archive.extract(arc, self.tmp / "o", items=["My Files/a.txt"])
        (self.tmp / "o" / "My Files" / "a.txt").write_text("mine")
        archive.extract(arc, self.tmp / "o", items=["My Files/a.txt"])
        self.assertEqual((self.tmp / "o" / "My Files" / "a.txt").read_text(), "mine")
        self.assertEqual(len(list((self.tmp / "o" / "My Files").iterdir())), 2)

    # --- passwords ----------------------------------------------------------
    def test_zip_aes_password(self) -> None:
        arc = self.make("zip", password="s3cret pass")
        info = archive.list_archive(arc)            # zip names are visible
        self.assertTrue(info.has_encrypted)
        with self.assertRaises(PasswordRequired):
            archive.extract(arc, self.tmp / "x")
        with self.assertRaises(WrongPassword):
            archive.extract(arc, self.tmp / "x", password="nope")
        archive.extract(arc, self.tmp / "ok", password="s3cret pass")
        self.assertEqual((self.tmp / "ok" / "My Files" / "a.txt").read_text(), "hello")

    def test_7z_encrypted_names(self) -> None:
        arc = self.make("7z", password="pw", encrypt_names=True)
        with self.assertRaises(PasswordRequired):
            archive.list_archive(arc)
        with self.assertRaises(WrongPassword):
            archive.list_archive(arc, password="bad")
        self.assertEqual(len(archive.list_archive(arc, password="pw").files), 4)

    # --- other formats ------------------------------------------------------
    def test_tar_and_tar_gz(self) -> None:
        for mode, name in (("w", "t.tar"), ("w:gz", "t.tar.gz"), ("w:xz", "t.txz")):
            with self.subTest(name=name):
                path = self.tmp / name
                with tarfile.open(path, mode) as tar:
                    tar.add(self.src, arcname="My Files")
                info = archive.list_archive(path)
                self.assertIn("My Files/sub/deep/c.txt", self.paths(info))
                out = archive.extract(path, self.tmp / f"out-{name}", items=["My Files/sub"])
                self.assertTrue((out / "My Files" / "sub" / "b.txt").is_file())
                self.assertFalse((out / "My Files" / "a.txt").exists())

    def test_single_gz(self) -> None:
        import gzip
        path = self.tmp / "notes.txt.gz"
        with gzip.open(path, "wb") as handle:
            handle.write(b"just one file")
        info = archive.list_archive(path)
        self.assertEqual(info.format, "gz")
        out = archive.extract(path, self.tmp / "gz")
        self.assertEqual((out / "notes.txt").read_bytes(), b"just one file")

    def test_rar(self) -> None:
        info = archive.list_archive(DATA / "rar3-subdirs.rar")
        self.assertEqual(info.format, "rar")
        self.assertIn("sub/with space/long fn.txt", self.paths(info))
        archive.extract(DATA / "rar3-subdirs.rar", self.tmp / "rar")
        self.assertTrue((self.tmp / "rar" / "sub" / "dir1" / "file1.txt").is_file())

    def test_rar_multi_volume(self) -> None:
        out = archive.extract(DATA / "rar5-vols.part1.rar", self.tmp / "vols")
        self.assertEqual((out / "vols" / "bigfile.txt").stat().st_size, 205000)

    def test_rar_passwords(self) -> None:
        with self.assertRaises(PasswordRequired):
            archive.extract(DATA / "rar5-psw-blake.rar", self.tmp / "p")
        archive.extract(DATA / "rar5-psw-blake.rar", self.tmp / "p", password="password")
        with self.assertRaises(PasswordRequired):
            archive.list_archive(DATA / "rar5-hpsw.rar")
        self.assertEqual(len(archive.list_archive(DATA / "rar5-hpsw.rar", "password").files), 2)

    def test_malicious_archive_stays_inside(self) -> None:
        """A RAR with a symlink trick must not write outside the target folder."""
        target = self.tmp / "inside"
        try:
            archive.extract(DATA / "rar5-evil-symlink-traversal.rar", target)
        except ArchiveError:
            pass  # refusing is fine too
        outside = [p for p in self.tmp.rglob("pwned.txt") if target not in p.parents]
        self.assertEqual(outside, [])

    # --- errors and cancel ---------------------------------------------------
    def test_not_an_archive_and_damaged(self) -> None:
        with self.assertRaises(ArchiveError) as ctx:
            archive.list_archive(self.src / "a.txt")
        self.assertIn("not a supported archive", ctx.exception.message)

        arc = self.make("zip")
        broken = self.tmp / "broken.zip"
        broken.write_bytes(arc.read_bytes()[:-60])
        with self.assertRaises(ArchiveError):
            archive.extract(broken, self.tmp / "broken")

    def test_cancel_create(self) -> None:
        big = self.src / "big.bin"
        big.write_bytes(os.urandom(60 * 1024 * 1024))
        token = CancelToken()
        threading.Timer(0.5, token.cancel).start()
        out = self.tmp / "big.7z"
        start = time.monotonic()
        with self.assertRaises(Cancelled):
            archive.create(CreateOptions([self.src], out, "7z", "maximum"), cancel=token)
        self.assertLess(time.monotonic() - start, 10)
        self.assertFalse(out.exists())
        self.assertFalse(out.with_name(out.name + ".part").exists())

    def test_default_extract_dir(self) -> None:
        self.assertEqual(archive.default_extract_dir(self.tmp / "a.tar.gz").name, "a")
        self.assertEqual(archive.default_extract_dir(self.tmp / "m.part1.rar").name, "m")
        (self.tmp / "photos").mkdir()
        (self.tmp / "photos" / "x").write_text("x")
        self.assertEqual(archive.default_extract_dir(self.tmp / "photos.zip").name, "photos (2)")


if __name__ == "__main__":
    unittest.main()
