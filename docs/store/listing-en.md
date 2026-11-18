# Microsoft Store listing — English (en-us)

Store page: https://apps.microsoft.com/detail/9N8M5LXDDBNL  (Store ID 9N8M5LXDDBNL)

Copy each block into Partner Center → your app → Store listings → English.

## Product name
Qapshyq

## Description
Qapshyq is a modern, free archive manager that opens and creates archives in a few clicks — with a clean interface, dark and light themes, and complete privacy.

Drag an archive onto the window to see what is inside: file names, sizes, dates and types, without extracting anything. Search inside the archive, double-click a file to open it, then extract everything or only the files you selected. Existing files are never overwritten.

Drag files or folders onto the window to compress them into ZIP or 7Z. Choose Fast, Normal or Maximum compression and protect your archive with a strong AES-256 password. For 7Z archives you can even hide the file names.

Everything works offline. Qapshyq has no accounts, no ads and no tracking — your files never leave your computer.

Supported formats:
• Open: ZIP, RAR (including RAR5 and multi-part archives), 7Z, TAR, GZ, TAR.GZ, TAR.XZ, TAR.BZ2, XZ, BZ2, CAB, ISO
• Create: ZIP and 7Z

Qapshyq is powered by the proven open-source 7-Zip engine. Its name comes from the Kazakh word "qapshyq" — a small pouch for keeping things safe.

## What's new in this version
First release: open, preview, search and extract archives; create ZIP and 7Z with AES-256 passwords; progress bar with Cancel; dark and light themes.

## Product features (one per line)
Open ZIP, RAR, 7Z, TAR and GZ archives with drag and drop
See the file list without extracting anything
Search inside archives and open single files with a double-click
Extract everything or only the selected files
Create ZIP and 7Z archives with Fast, Normal or Maximum compression
Protect archives with AES-256 passwords
Hide file names in password-protected 7Z archives
Never overwrites your existing files
Progress bar, Cancel button and clear error messages
Dark and light themes
Works completely offline — no accounts, ads or tracking
Powered by the open-source 7-Zip engine

## Search terms (max 7)
zip
rar
7z
unzip
archive
extract
compress

## Copyright and trademark info
© 2026 Byjuma

## Additional license terms
Qapshyq is free and open source under the MIT license. It includes 7-Zip (GNU LGPL with the unRAR restriction) and Qt for Python (LGPL v3). https://github.com/Jumabyek/qapshyq/blob/main/THIRD_PARTY_NOTICES.md

## Screenshots (Desktop, PNG 1600×900)
docs/store/screenshots/1-home-dark.png — "Drop an archive to open it, or files to compress them"
docs/store/screenshots/2-archive-dark.png — "See what is inside without extracting"
docs/store/screenshots/3-search-light.png — "Search inside archives"
docs/store/screenshots/4-progress-light.png — "Clear progress with a Cancel button"
docs/store/screenshots/5-create-dark.png — "Create ZIP or 7Z with AES-256 passwords"
docs/store/screenshots/6-password-light.png — "Open password-protected archives"

## Store logo
installer/msix/StoreListingLogo-300.png (300×300)

---

# Properties page
- Category: **Utilities & tools** → Subcategory: **File managers**
- Privacy policy URL: https://github.com/Jumabyek/qapshyq/blob/main/PRIVACY.md
- Website: https://github.com/Jumabyek/qapshyq
- Support contact info: https://github.com/Jumabyek/qapshyq/issues
- This product accesses, collects or transmits personal information: **No**

# Pricing and availability
- Price: **Free**
- Markets: all markets

# Age ratings (IARC questionnaire)
- Category: **Utility / productivity app**. Answer **No** to all content questions (no violence, no user communication, no sharing of location, no purchases). Expected rating: 3+ / Everyone.

# Submission options → restricted capability justification (runFullTrust)
Qapshyq is a classic Win32 desktop application (Python + Qt/PySide6) packaged as MSIX. It runs the bundled 7-Zip command-line engine (7z.exe) as a child process to read and write archive files in folders the user chooses. This requires the runFullTrust capability that all packaged Win32 desktop apps use.

# Notes for certification
Free, offline archive manager. No account, sign-in or internet connection is needed. To test: launch Qapshyq, drag any .zip, .7z or .rar file onto the window (or click "Open archive…") to see its contents, then click "Extract all". To create an archive, click "Create archive…", add a folder and click "Create".
