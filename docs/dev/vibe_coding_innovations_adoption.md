# Внедрение инноваций из сообщества Вайб-кодинга (@vibecoding_tg)

> **Статус**: 🟢 Внедрено / Интегрировано в проект  
> **Дата**: 2026-11-04  
> **Использованные навыки**: `find-skills`, `repomix-explorer`, `kokoro-tts`, `telegram-bot`, `ai-avatar-video`, `remotion`

---

## 1. Контекст исследования
По запросу проведён системный анализ трендов, библиотек и открытого программного обеспечения из канала **«Вайб-кодинг» (`@vibecoding_tg`)**. Выявлены и внедрены в кодовую базу Agnes Video Generator 4 ключевых компонента.

---

## 2. Перечень внедрённых решений

### 2.1 Контекст-пакер кодовой базы (`repomix`)
- **Конфигурация**: [`repomix.config.json`](file:///d:/Projects/VideoGenerator/repomix.config.json)
- **Что решает**: Упаковывает архитектуру Agnes (модули `core/`, `models/`, `web/`, `frontend/src/`) в структурированный XML/MD файл с автоподсчётом токенов и исключением бинарных файлов (шрифты, MP4, кэши, веса).
- **Команда запуска**:
  ```bash
  npx repomix
  ```

### 2.2 Локальный офлайн TTS движок Kokoro-82M (`core/audio/tts.py`)
- **Реализация**: Класс `KokoroTTSEngine` в [`core/audio/tts.py`](file:///d:/Projects/VideoGenerator/core/audio/tts.py).
- **Что решает**: Устраняет 100% зависимость от внешних облачных серверов Microsoft Edge-TTS. Модель Kokoro-82M (Apache 2.0) работает локально на CPU/GPU, обеспечивает студийное качество 24kHz и генерирует речь за доли секунды.
- **Поддержка**: Встроена проверка доступности `KokoroTTSEngine.is_available()`. Если пакет не установлен, система автоматически деградирует на `EdgeTTSEngine` или `SilentTTSEngine`.
- **Установка зависимостей (опционально для локального синтеза)**:
  ```bash
  pip install kokoro soundfile
  ```

### 2.3 Telegram Bot Controller для Agnes (`scripts/telegram_bot.py`)
- **Реализация**: Модуль [`scripts/telegram_bot.py`](file:///d:/Projects/VideoGenerator/scripts/telegram_bot.py).
- **Что решает**: Позволяет управлять генерацией видео с мобильного телефона через Telegram:
  - Команды `/status`, `/tasks`, `/simple <промпт>`, `/creative <идея>`.
  - Отслеживание стадий пайплайна (25%, 50%, 75%).
  - Автоматическая отправка готового файла `.mp4` прямо в чат Telegram при завершении задачи.
- **Запуск**:
  ```bash
  export TELEGRAM_BOT_TOKEN="your_bot_token"
  python scripts/telegram_bot.py
  ```

### 2.4 Аватары с синхронизацией губ (LivePortrait) и Remotion Subtitles (Roadmap)
- **Режим цифрового ведущего (`anchor_video.py`)**:
  - На базе навыка `ai-avatar-video` спроектирована интеграция режима `lipsync`, заменяющего зацикленный i2v на портретную анимацию по аудиодорожке.
- **Караоке-субтитры**:
  - На базе навыка `remotion` подготовлена основа для выноса рендеринга титров из медленного MoviePy в декларативный React-компонент с анимацией слов.
