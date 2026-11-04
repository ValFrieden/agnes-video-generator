@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
echo ============================================================
echo   Генерация 12 кейнфреймов для «Беги за солнцем» (Жёлтый зонт)
echo ============================================================
.venv\Scripts\python.exe begi_clip_pipeline.py --stage keyframes
pause
