# Обзор проекта (на 27.10.2026)

## Цель
Анимированный музыкальный клип к песне «Masha - S dnem Rozdenija.mp3» (3:07, Downloads пользователя). В кадре **только Маша**: стилизованная 3D-героиня по реальным фото (светло-голубая рубашка, длинные тёмно-каштановые волосы с пробором, карие глаза). Сценарий на 27 шотов (187 с). Делается в Google Flow (Veo 3.1 Fast для видео, Nano Banana для картинок) через автоматизацию браузера.

## Где что лежит (`D:\Projects\VideoGenerator`)
- Сценарий: `С днём рождения, Маша — сценарий клипа (Google Flow).md`; правила: `ПРАВИЛА_КЛИПА.md` (раздел 6 = ограничения Flow).
- Референсы Маши: `masha_frames/ref/` (фото; `masha_01_blue_shirt_crop.jpg` без водяного знака, оригинал не использовать), `masha_frames/old_project/` (карта героини `01_turnaround.jpg`, эмоции, предметы).
- 16:9 кадры: `masha_frames/wide_16x9/` (`wide_01.jpg` фото, `wide_02.jpg` старый keyframe), `masha_frames/morph/` (`toon_aligned.jpg`, `morph_s01.mp4`).
- Клипы: `masha_frames/clips/` (`clip_02.mp4`, дальше `clip_NN.mp4`), keyframe и кадры сцен: `masha_frames/sNN/`.
- Состояние: `flow_state/shots.json` (статусы шотов), `flow_state/credits.jsonl` (журнал кредитов), `flow_accounts.json` (счета).
- Код Flow: `core/api/google_flow_engine.py`, `core/api/google_flow_ui.py`, `core/flow_*.py` (см. `pipeline-tools.md`).

## Счета и проект Flow
- Рабочий счёт «second»: проект `0559cf6d-d69a-4ba0-a214-0b4c5d6c0c81`, URL `https://flow.google.com/u/0/project/<id>` (индекс 0 в текущем Chrome; раньше 3, Flow перенаправляет).
- Баланс: **990 кредитов** после S02. Первый аккаунт почти пуст (~80 кредитов), не использовать.
- План: 27 клипов × 20 = 540 кредитов; клипы Veo Quality могут стоить больше (не проверено).
- Chrome с отладочным портом 9222: профиль `User Data Flow`, запуск `tools/google-flow-browser-mcp/launch_chrome.ps1`. Закрывается вместе с приложением.

## Окружение
Windows 11, Git Bash и PowerShell, Python venv `.venv` (playwright 1.64, opencv-python-headless, Pillow), ffmpeg в PATH, ветка git `fix/google-flow-p0-cost-guard`. Ничего из новой работы не закоммичено (коммит только по просьбе автора).
