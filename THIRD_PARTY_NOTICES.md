# Third-party notices

Qapshyq's own code is MIT-licensed (see `LICENSE`). It ships with these components:

## 7-Zip (archive engine)
- Author: Igor Pavlov — https://www.7-zip.org — source: https://github.com/ip7z/7zip
- License: GNU LGPL, with the **unRAR license restriction** for the RAR decoder,
  plus BSD 2/3-clause for a few files. Full text: `bin/7-Zip-License.txt`.
- Qapshyq runs the unmodified 7-Zip program (`7z.exe` + `7z.dll` / `7zz`) as a separate process.
- **unRAR restriction:** the RAR decompression code may not be used to develop a
  RAR (WinRAR) compatible archiver. Qapshyq therefore only *extracts* RAR archives
  and never creates them.

## Qt for Python (PySide6) and Qt
- https://www.qt.io/qt-for-python — License: GNU LGPL v3.
- Qt libraries are shipped as separate shared libraries that users may replace.
  Source code: https://code.qt.io/

## Python
- https://www.python.org — License: PSF License.

## Test files
- `tests/data/*.rar` come from the test suite of the *rarfile* project (ISC license,
  see `tests/data/RAR_SAMPLES_LICENSE.txt`). They are used only by automated tests.
