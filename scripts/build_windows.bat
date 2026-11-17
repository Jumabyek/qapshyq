@echo off
rem ---------------------------------------------------------------------------
rem  Build Qapshyq for Windows:
rem    dist\Qapshyq\Qapshyq.exe            (the app folder)
rem    dist\Qapshyq-Setup-1.0.0.exe        (the installer, needs Inno Setup 6)
rem  Usage:  scripts\build_windows.bat
rem ---------------------------------------------------------------------------
setlocal
cd /d "%~dp0\.."

call scripts\setup_windows.bat || exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt --quiet || exit /b 1

echo Running tests...
.venv\Scripts\python.exe -m unittest discover -s tests || exit /b 1

echo Building the app with PyInstaller...
.venv\Scripts\pyinstaller.exe --noconfirm --clean qapshyq.spec || exit /b 1

set ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" set ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe
if exist "%ISCC%" (
    echo Building the installer with Inno Setup...
    "%ISCC%" installer\qapshyq.iss || exit /b 1
    echo.
    echo Done! Installer: dist\
) else (
    echo.
    echo App built in dist\Qapshyq\ - to also make Setup.exe, install Inno Setup 6
    echo from https://jrsoftware.org/isdl.php and run this script again.
)
