#!/usr/bin/env python3
"""scripts/telegram_bot.py — Telegram Bot контроллер для Agnes Video Generator.

Позволяет запускать генерацию видео, отслеживать прогресс и получать готовые MP4 прямо в Telegram.
Основан на стандарте Telegram Bot API и шаблонах из навыка telegram-bot.

Использование:
    export TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    python scripts/telegram_bot.py
    
Опциональные переменные окружения:
    AGNES_API_URL: адрес сервера Agnes (по умолчанию: http://localhost:8765)
    TELEGRAM_ALLOWED_USERS: список разрешенных user_id через запятую (для приватного доступа)
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [TelegramBot] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("telegram_bot")

DEFAULT_API_URL = os.environ.get("AGNES_API_URL", "http://localhost:8765").rstrip("/")


class TelegramAPI:
    """Легковесный асинхронный клиент для Telegram Bot API без внешних зависимостей."""

    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"

    async def _post_json(self, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{method}"
        payload = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        loop = asyncio.get_event_loop()

        def _exec():
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                logger.error(f"Telegram API HTTP error {e.code}: {err_body}")
                return {"ok": False, "description": err_body}
            except Exception as e:
                logger.error(f"Telegram API network error: {e}")
                return {"ok": False, "description": str(e)}

        return await loop.run_in_executor(None, _exec)

    async def get_updates(self, offset: Optional[int] = None, timeout: int = 25) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/getUpdates?timeout={timeout}"
        if offset is not None:
            url += f"&offset={offset}"
        req = urllib.request.Request(url, headers={"User-Agent": "AgnesTelegramBot/1.0"})
        loop = asyncio.get_event_loop()

        def _exec():
            try:
                with urllib.request.urlopen(req, timeout=timeout + 10) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    return res.get("result", []) if res.get("ok") else []
            except Exception as e:
                logger.debug(f"get_updates timeout/error: {e}")
                return []

        return await loop.run_in_executor(None, _exec)

    async def send_message(self, chat_id: int, text: str, parse_mode: Optional[str] = "Markdown") -> Dict[str, Any]:
        data = {"chat_id": chat_id, "text": text}
        if parse_mode:
            data["parse_mode"] = parse_mode
        return await self._post_json("sendMessage", data)

    async def send_video(self, chat_id: int, video_path: str, caption: str = "") -> bool:
        """Отправляет локальный MP4 файл в чат с использованием multipart/form-data."""
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return False

        url = f"{self.base_url}/sendVideo"
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        loop = asyncio.get_event_loop()

        def _upload():
            import mimetypes
            filename = os.path.basename(video_path)
            mime_type = mimetypes.guess_type(video_path)[0] or "video/mp4"

            with open(video_path, "rb") as f:
                file_bytes = f.read()

            body = bytearray()
            # chat_id
            body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{chat_id}\r\n".encode())
            # caption
            if caption:
                body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{caption}\r\n".encode())
            # file
            body.extend(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"video\"; filename=\"{filename}\"\r\nContent-Type: {mime_type}\r\n\r\n".encode()
            )
            body.extend(file_bytes)
            body.extend(f"\r\n--{boundary}--\r\n".encode())

            req = urllib.request.Request(
                url,
                data=bytes(body),
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    return res.get("ok", False)
            except Exception as e:
                logger.error(f"Failed to upload video: {e}")
                return False

        return await loop.run_in_executor(None, _upload)


class AgnesClient:
    """Клиент для REST API сервера Agnes Video Generator."""

    def __init__(self, base_url: str):
        self.base_url = base_url

    async def get_config(self) -> Dict[str, Any]:
        return await self._get("/api/config")

    async def list_tasks(self) -> Dict[str, Any]:
        return await self._get("/api/tasks")

    async def get_task(self, task_id: str) -> Dict[str, Any]:
        return await self._get(f"/api/tasks/{task_id}")

    async def create_simple_task(self, prompt: str, mode: str = "t2v") -> Dict[str, Any]:
        return await self._post("/api/tasks/simple", {"prompt": prompt, "mode": mode})

    async def create_creative_task(self, idea: str) -> Dict[str, Any]:
        return await self._post("/api/tasks/creative", {"idea": idea})

    async def _get(self, path: str) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        loop = asyncio.get_event_loop()

        def _exec():
            try:
                with urllib.request.urlopen(url, timeout=10) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                return {"ok": False, "error": str(e)}

        return await loop.run_in_executor(None, _exec)

    async def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        loop = asyncio.get_event_loop()

        def _exec():
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                return {"ok": False, "error": e.read().decode("utf-8", errors="replace")}
            except Exception as e:
                return {"ok": False, "error": str(e)}

        return await loop.run_in_executor(None, _exec)


class BotRunner:
    def __init__(self, token: str, agnes_url: str, allowed_users: Optional[List[int]] = None):
        self.tg = TelegramAPI(token)
        self.agnes = AgnesClient(agnes_url)
        self.allowed_users = allowed_users
        self.tracking_tasks: Dict[str, int] = {}  # task_id -> chat_id

    def is_user_allowed(self, user_id: int) -> bool:
        if not self.allowed_users:
            return True
        return user_id in self.allowed_users

    async def handle_message(self, msg: Dict[str, Any]):
        chat_id = msg.get("chat", {}).get("id")
        user_id = msg.get("from", {}).get("id")
        text = msg.get("text", "").strip()

        if not chat_id or not text:
            return

        if not self.is_user_allowed(user_id):
            await self.tg.send_message(chat_id, "⛔ Доступ запрещён. Ваш user_id не в списке доверенных.")
            return

        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ("/start", "/help"):
            welcome = (
                "🎬 *Agnes Video Generator Bot*\n\n"
                "Команды управления:\n"
                "• `/status` — Проверить статус сервера Agnes\n"
                "• `/tasks` — Список последних задач\n"
                "• `/simple <промпт>` — Создать быстрое видео (t2v)\n"
                "• `/creative <идея>` — Создать сюжетный ролик (сценарий + озвучка)\n"
                "• `/track <task_id>` — Отслеживать статус задачи вручную\n"
            )
            await self.tg.send_message(chat_id, welcome)

        elif cmd == "/status":
            cfg = await self.agnes.get_config()
            if cfg.get("ok"):
                has_key = cfg.get("has_api_key", False)
                active = cfg.get("active_pipeline_count", 0)
                await self.tg.send_message(
                    chat_id,
                    f"✅ *Сервер активен*\n• API Key настроен: `{has_key}`\n• Активных задач: `{active}`\n• URL: `{self.agnes.base_url}`",
                )
            else:
                await self.tg.send_message(chat_id, f"❌ Сервер недоступен: {cfg.get('error')}")

        elif cmd == "/tasks":
            res = await self.agnes.list_tasks()
            tasks = res.get("tasks", []) if isinstance(res, dict) else []
            if not tasks:
                await self.tg.send_message(chat_id, "📭 Нет активных или завершенных задач.")
                return

            lines = ["📋 *Последние задачи:*"]
            for t in tasks[:7]:
                tid = t.get("task_id", "")[:8]
                status = t.get("status", "unknown")
                ttype = t.get("task_type", "")
                progress = int(t.get("progress", 0) * 100)
                icon = "🟢" if status == "completed" else "⏳" if status == "running" else "🔴" if status == "failed" else "⚪"
                lines.append(f"{icon} `{tid}` | *{ttype}* | {status} ({progress}%)")
            await self.tg.send_message(chat_id, "\n".join(lines))

        elif cmd == "/simple":
            if not arg:
                await self.tg.send_message(chat_id, "Укажите промпт. Пример:\n`/simple Кот космонавт летит на Марс`")
                return
            await self.tg.send_message(chat_id, f"🚀 Запускаю создание простого видео:\n_\"{arg}\"_")
            res = await self.agnes.create_simple_task(arg)
            if res.get("task_id"):
                tid = res["task_id"]
                await self.tg.send_message(chat_id, f"✅ Задача создана: `{tid}`\nОтслеживаю выполнение...")
                asyncio.create_task(self.poll_task_completion(chat_id, tid))
            else:
                await self.tg.send_message(chat_id, f"❌ Ошибка создания: {res.get('error', 'Unknown error')}")

        elif cmd == "/creative":
            if not arg:
                await self.tg.send_message(chat_id, "Укажите идею. Пример:\n`/creative Загадочное исчезновение маячника`")
                return
            await self.tg.send_message(chat_id, f"✨ Запускаю креативный сценарий:\n_\"{arg}\"_")
            res = await self.agnes.create_creative_task(arg)
            if res.get("task_id"):
                tid = res["task_id"]
                await self.tg.send_message(chat_id, f"✅ Креативная задача создана: `{tid}`\nОтслеживаю выполнение...")
                asyncio.create_task(self.poll_task_completion(chat_id, tid))
            else:
                await self.tg.send_message(chat_id, f"❌ Ошибка создания: {res.get('error', 'Unknown error')}")

        elif cmd == "/track":
            if not arg:
                await self.tg.send_message(chat_id, "Укажите ID задачи: `/track <task_id>`")
                return
            asyncio.create_task(self.poll_task_completion(chat_id, arg.strip()))
            await self.tg.send_message(chat_id, f"🔍 Начато отслеживание задачи `{arg.strip()}`")

    async def poll_task_completion(self, chat_id: int, task_id: str):
        last_progress_bucket = -1
        while True:
            await asyncio.sleep(5)
            data = await self.agnes.get_task(task_id)
            if not data or not data.get("ok", True):
                continue

            task = data.get("task", data)
            status = task.get("status")
            progress = float(task.get("progress", 0.0))
            current_bucket = int(progress * 4)  # 0, 1(25%), 2(50%), 3(75%), 4(100%)

            # Оповещение при преодолении четвертей прогресса
            if current_bucket > last_progress_bucket and current_bucket in (1, 2, 3):
                last_progress_bucket = current_bucket
                pct = int(progress * 100)
                await self.tg.send_message(chat_id, f"⏳ Задача `{task_id[:8]}`: прогресс {pct}%...")

            if status == "completed":
                video_url = task.get("video_url", "")
                await self.tg.send_message(chat_id, f"🎉 *Видео готово!* (Задача `{task_id[:8]}`)")
                
                # Попробуем найти локальный файл на диске
                local_path = None
                if video_url:
                    candidate = os.path.join(".", video_url.lstrip("/"))
                    if os.path.exists(candidate):
                        local_path = candidate

                if local_path:
                    await self.tg.send_message(chat_id, "📤 Загружаю MP4 видео...")
                    success = await self.tg.send_video(chat_id, local_path, caption=f"🎬 Agnes Video `{task_id[:8]}`")
                    if not success:
                        await self.tg.send_message(chat_id, f"Ссылка на скачивание: {self.agnes.base_url}{video_url}")
                else:
                    await self.tg.send_message(chat_id, f"Ссылка на результат: {self.agnes.base_url}{video_url}")
                break

            elif status == "failed":
                err = task.get("error", "Неизвестная ошибка")
                await self.tg.send_message(chat_id, f"❌ Задача `{task_id[:8]}` завершилась с ошибкой:\n`{err}`")
                break

    async def run(self):
        logger.info(f"Запуск Telegram Bot polling (Agnes API: {self.agnes.base_url})...")
        offset = None
        while True:
            try:
                updates = await self.tg.get_updates(offset=offset, timeout=20)
                for update in updates:
                    offset = update["update_id"] + 1
                    msg = update.get("message")
                    if msg:
                        await self.handle_message(msg)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                await asyncio.sleep(5)


def main():
    parser = argparse.ArgumentParser(description="Agnes Video Generator Telegram Bot")
    parser.add_argument("--token", default=os.environ.get("TELEGRAM_BOT_TOKEN"), help="Telegram Bot Token")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="Agnes Server URL")
    parser.add_argument("--allowed-users", default=os.environ.get("TELEGRAM_ALLOWED_USERS"), help="Allowed user IDs (comma separated)")
    args = parser.parse_args()

    if not args.token:
        logger.error("TELEGRAM_BOT_TOKEN не задан! Задайте переменную окружения или передайте флаг --token.")
        print("\nИспользование:")
        print("  export TELEGRAM_BOT_TOKEN=\"your_bot_token\"")
        print("  python scripts/telegram_bot.py\n")
        sys.exit(1)

    allowed = [int(u.strip()) for u in args.allowed_users.split(",") if u.strip().isdigit()] if args.allowed_users else None

    runner = BotRunner(token=args.token, agnes_url=args.api_url, allowed_users=allowed)
    asyncio.run(runner.run())


if __name__ == "__main__":
    main()
