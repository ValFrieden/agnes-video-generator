# Код и инструменты

## Модули (все в `core/`)
| Файл | Роль |
|---|---|
| `api/google_flow_engine.py` | движок Playwright/CDP: attach, prompt, submit, карточка цены, `confirm_within_budget`, скачивание, `generate_scene`, `generate_image`, `read_credit_balance` |
| `api/google_flow_ui.py` | **единственное место селекторов** Flow |
| `flow_shot_state.py` | `shots.json`: статусы PLANNED→…→DOWNLOADED, запрет повторной отправки (`ShotAlreadySubmittedError`), `new_version()` |
| `flow_budget.py` | `BudgetPolicy` (лимит на клип, общий бюджет, резерв), `CreditLedger` (`credits.jsonl`), `FlowAccounts` (`flow_accounts.json`) |
| `flow_frames.py` | проверка кадров (16:9, чёрные полосы), `alignment_score` совпадения композиции |
| `flow_transitions.py` | ffmpeg-морфинг фото→3D (8 с за ~3 с), контрольный лист кадров |
| `flow_prompts.py` | шаблоны запросов, нормализация длительности до 8 с |
| `flow_pipeline.py` | команда `python -m core.flow_pipeline …` |

## Команды (из корня проекта, Git Bash)
```bash
.venv/Scripts/python.exe -m core.flow_pipeline status
.venv/Scripts/python.exe -m core.flow_pipeline balance
.venv/Scripts/python.exe -m core.flow_pipeline check --a кадр.jpg [--b второй.jpg]
.venv/Scripts/python.exe -m core.flow_pipeline image --prompt "..." --ref a.jpg --ref b.png --out masha_frames/sNN/sNN_keyframe.jpg [--same-composition]
.venv/Scripts/python.exe -m core.flow_pipeline video --shot SNN --frame masha_frames/sNN/sNN_keyframe.jpg --motion "..." --out masha_frames/clips/clip_NN.mp4
.venv/Scripts/python.exe -m core.flow_pipeline morph --photo a.jpg --toon b.jpg --out m.mp4 --sheet sheet.jpg
.venv/Scripts/python.exe -m core.flow_pipeline sheet --video clip.mp4 --out sheet.jpg --times 0.3,2,4,6,7.7
```
Коды возврата `video`: 0 готово, 1 не готов/плохой кадр, 2 остановлено (бюджет, вопрос агента), 3 шот уже отправлялся.

## Тесты
- Быстрый набор по Flow (~4 с):  
  `.venv/Scripts/python.exe -m pytest tests/test_flow_*.py tests/test_google_flow.py -q --basetemp=C:/Users/Valeri/AppData/Local/Temp/claude/D--Projects-VideoGenerator/b35bf077-4455-46eb-b04a-3924ddfb1400/scratchpad/pt -p no:cacheprovider`  
  (`--basetemp` нужен: стандартный Temp запрещён правами).
- `tests/test_flow_selectors_dom.py` проверяет селекторы на HTML, имитирующем Flow, **через живой Chrome :9222**; без Chrome тесты пропускаются.
- `pytest -k flow` по всей папке `tests` собирает весь проект (~1 мин), поэтому указывать файлы.
- Весь набор проекта: 4 падения вне Flow (`test_config_settings` ×2, `test_ffmpeg_tool`, `test_gallery_routes`), не из-за наших изменений.

## Omni R2V и пересъёмка (30.10.2026)
- CLI `flow_pipeline video` всегда шлёт «Veo 3.1 Fast» и один стартовый кадр. Для Omni использовался одноразовый скрипт: `GoogleFlowEngine.generate_scene(prompt=…, reference_image_path=<keyframe>, extra_references=[01_turnaround.jpg], prompt_as_is=True, shot_store, shot_id, policy, ledger, account)`. Промпт начинается «Generate a video with Omni 1.1 Flash using Reference-to-Video (R2V), 8 seconds, 16:9 landscape.», затем «FIRST attached image is the start composition, SECOND is the character sheet», движение, запрет речи, `STYLE_BLOCK`, `ONE_CHARACTER`. Скрипты лежали во временной папке сессии и не сохранены; при необходимости воспроизвести по этому описанию (стоит добавить `--model` в CLI).
- Новая версия шота: `ShotStateStore.new_version('S17', reason='…')`; статус вручную: `advance('S19', ShotStatus.RENDERED)`, затем `advance('S19', ShotStatus.DOWNLOADED, clip=…)`.
- Скачать уже готовый клип без новой отправки: `GoogleFlowEngine.download_latest_video(path)` после `open_project`.

## Chrome
`powershell -File tools/google-flow-browser-mcp/launch_chrome.ps1` (профиль `User Data Flow`, порт 9222); проверка `curl http://127.0.0.1:9222/json/version`.
