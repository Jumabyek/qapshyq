@echo off
rem ---------------------------------------------------------------------------
rem  Qapshyq setup for Windows: Python packages + the 7-Zip engine.
rem  Safe to run many times. Usage:  scripts\setup_windows.bat
rem ---------------------------------------------------------------------------
setlocal
cd /d "%~dp0\.."
set SEVENZIP_VERSION=2606

rem --- 1. Find Python (the "py" launcher comes with python.org installers) ---
set PY=
where py >nul 2>nul && set PY=py -3
if not defined PY (
    where python >nul 2>nul && set PY=python
)
if not defined PY (
    echo [!] Python was not found. Install Python 3.12+ from https://www.python.org/downloads/
    echo     and tick "Add python.exe to PATH" during installation.
    exit /b 1
)

rem --- 2. Virtual environment with the packages --------------------------------
if not exist .venv\Scripts\python.exe (
    echo Creating virtual environment...
    %PY% -m venv .venv || exit /b 1
)
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.venv\Scripts\python.exe -m pip install -r requirements.txt --quiet || exit /b 1

rem --- 3. 7-Zip engine into bin\ ------------------------------------------------
if exist bin\7z.exe if exist bin\7z.dll (
    echo 7-Zip engine already in bin\
    goto done
)
if exist "%ProgramFiles%\7-Zip\7z.exe" (
    echo Copying 7-Zip from "%ProgramFiles%\7-Zip"...
    copy /y "%ProgramFiles%\7-Zip\7z.exe" bin\ >nul
    copy /y "%ProgramFiles%\7-Zip\7z.dll" bin\ >nul
    goto done
)
echo Downloading 7-Zip %SEVENZIP_VERSION% from the official site 7-zip.org...
set MSI=%TEMP%\7z%SEVENZIP_VERSION%-x64.msi
set UNPACK=%TEMP%\qapshyq-7zip
curl -fL -o "%MSI%" https://www.7-zip.org/a/7z%SEVENZIP_VERSION%-x64.msi || goto fail
rem "msiexec /a" only unpacks the files: nothing is installed, no admin needed.
msiexec /a "%MSI%" /qn TARGETDIR="%UNPACK%" || goto fail
copy /y "%UNPACK%\Files\7-Zip\7z.exe" bin\ >nul || goto fail
copy /y "%UNPACK%\Files\7-Zip\7z.dll" bin\ >nul || goto fail
rmdir /s /q "%UNPACK%"
del "%MSI%"

:done
echo.
echo Setup complete. Start the app with:  run_windows.bat
exit /b 0

:fail
echo [!] Could not get 7-Zip automatically.
echo     Install it from https://www.7-zip.org and run this script again.
exit /b 1
