@echo off
REM SunSirs daily fetch for Windows Task Scheduler.
REM Program: this .bat
REM Start in: oil_data_ingest (or leave blank — we cd to repo root)

cd /d "%~dp0.."

set "PY="
if exist "%~dp0..\.venv\Scripts\python.exe" set "PY=%~dp0..\.venv\Scripts\python.exe"
if not defined PY set "PY=python"

echo [%DATE% %TIME%] Using: %PY%
echo [%DATE% %TIME%] Starting SunSirs fetch...
"%PY%" scripts\fetch_sunsirs.py
set ERR=%ERRORLEVEL%
echo [%DATE% %TIME%] Exit code %ERR%
exit /b %ERR%
