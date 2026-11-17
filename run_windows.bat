@echo off
rem Double-click to start Qapshyq on Windows (runs setup the first time).
cd /d "%~dp0"
if not exist .venv\Scripts\pythonw.exe goto setup
if not exist bin\7z.exe goto setup
goto run

:setup
call scripts\setup_windows.bat
if errorlevel 1 (
    pause
    exit /b 1
)

:run
start "" .venv\Scripts\pythonw.exe main.py %*
