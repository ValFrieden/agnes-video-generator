@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo   Begi Za Solntsem - Variant A (Yellow Umbrella) Pipeline
echo ============================================================
echo.

set "PYTHONPATH=%~dp0.venv\Lib\site-packages"

set "PY=py -3"
where py >nul 2>nul
if errorlevel 1 (
    if exist ".venv\Scripts\python.exe" (
        set "PY=.venv\Scripts\python.exe"
    ) else (
        set "PY=python"
    )
)

echo Running: %PY% begi_clip_pipeline.py %*
%PY% begi_clip_pipeline.py %*

echo.
pause
