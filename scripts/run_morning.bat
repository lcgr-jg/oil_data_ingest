@echo off
REM Weekday morning ingest: SunSirs spots then JLC cracks (Bloomberg).
REM Point Task Scheduler here (e.g. 09:20) before desk_reports china_fuels @ 09:30.

cd /d "%~dp0.."

set "PY="
if exist "%~dp0..\.venv\Scripts\python.exe" set "PY=%~dp0..\.venv\Scripts\python.exe"
if not defined PY if exist "%~dp0..\..\.venv\Scripts\python.exe" set "PY=%~dp0..\..\.venv\Scripts\python.exe"
if not defined PY set "PY=python"

echo [%DATE% %TIME%] Using: %PY%
echo [%DATE% %TIME%] SunSirs fetch...
"%PY%" scripts\fetch_sunsirs.py
set ERR1=%ERRORLEVEL%

echo [%DATE% %TIME%] JLC cracks fetch...
"%PY%" scripts\fetch_jlc_cracks.py
set ERR2=%ERRORLEVEL%

if %ERR1% NEQ 0 (
  echo [%DATE% %TIME%] SunSirs failed with %ERR1%
  exit /b %ERR1%
)
if %ERR2% NEQ 0 (
  echo [%DATE% %TIME%] JLC cracks failed with %ERR2%
  exit /b %ERR2%
)
echo [%DATE% %TIME%] Morning ingest OK
exit /b 0
