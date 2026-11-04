"""core.api.lipsync_provider — Поставщик синхронизации губ и мимики (Lip-Sync).

Поддерживает интеграцию с микросервисами LivePortrait / EchoMimic / SadTalker
для создания реалистичного видео цифрового ведущего (anchor_video) по статичному портрету и аудиофайлу.
"""

import asyncio
import logging
import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

DEFAULT_LIPSYNC_ENDPOINT = os.environ.get("LIPSYNC_ENDPOINT_URL", "http://localhost:8000/lipsync")


class LipSyncError(RuntimeError):
    """Базовое исключение для ошибок генерации lip-sync."""
    pass


class LipSyncUnavailableError(LipSyncError):
    """Исключение, сигнализирующее о недоступности микросервиса (для плавного отката)."""
    pass


class BaseLipSyncProvider(ABC):
    """Абстрактный контракт для провайдеров синхронизации губ."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Проверяет доступность сервиса."""
        pass

    @abstractmethod
    async def generate_lipsync(
        self,
        image_path: str,
        audio_path: str,
        output_path: str,
        **kwargs: Any,
    ) -> str:
        """Генерирует видео с синхронизированными губами и мимикой.

        Args:
            image_path: Исходное изображение лица (портрет)
            audio_path: Аудиодорожка речи (.mp3 / .wav)
            output_path: Путь для сохранения итогового .mp4
            **kwargs: Дополнительные параметры (fps, scale, face_crop)

        Returns:
            Путь к сохраненному видеофайлу output_path
        """
        pass


class LivePortraitService(BaseLipSyncProvider):
    """Клиент для REST API микросервиса LivePortrait / EchoMimic.
    
    Отправляет multipart/form-data запрос на эндпоинт генерации и сохраняет
    потоковый ответ в выходной файл .mp4.
    """

    def __init__(self, endpoint_url: Optional[str] = None):
        self.endpoint_url = (endpoint_url or DEFAULT_LIPSYNC_ENDPOINT).rstrip("/")

    async def is_available(self) -> bool:
        """Проверяет пинг/здоровье микросервиса."""
        health_url = f"{self.endpoint_url}/health"
        loop = asyncio.get_event_loop()

        def _ping() -> bool:
            try:
                req = urllib.request.Request(health_url, headers={"User-Agent": "AgnesLipSync/1.0"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    return resp.status in (200, 204)
            except Exception:
                # Попробуем GET на базовый URL
                try:
                    req_base = urllib.request.Request(self.endpoint_url, headers={"User-Agent": "AgnesLipSync/1.0"})
                    with urllib.request.urlopen(req_base, timeout=3) as resp:
                        return resp.status in (200, 404, 405)
                except Exception:
                    return False

        return await loop.run_in_executor(None, _ping)

    async def generate_lipsync(
        self,
        image_path: str,
        audio_path: str,
        output_path: str,
        **kwargs: Any,
    ) -> str:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"[LipSync] Image not found: {image_path}")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"[LipSync] Audio not found: {audio_path}")

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        logger.info(
            f"[LipSync] [LivePortrait] Submitting task to {self.endpoint_url}: "
            f"image={os.path.basename(image_path)}, audio={os.path.basename(audio_path)}"
        )

        loop = asyncio.get_event_loop()

        def _do_request() -> str:
            boundary = "----AgnesLipSyncBoundary987654321"
            body = bytearray()

            def add_file(field_name: str, file_path: str):
                filename = os.path.basename(file_path)
                mime = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
                with open(file_path, "rb") as f:
                    data = f.read()
                body.extend(f"--{boundary}\r\n".encode())
                body.extend(f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode())
                body.extend(f"Content-Type: {mime}\r\n\r\n".encode())
                body.extend(data)
                body.extend(b"\r\n")

            add_file("image", image_path)
            add_file("audio", audio_path)

            for k, v in kwargs.items():
                if v is not None:
                    body.extend(f"--{boundary}\r\n".encode())
                    body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
                    body.extend(str(v).encode())
                    body.extend(b"\r\n")

            body.extend(f"--{boundary}--\r\n".encode())

            req = urllib.request.Request(
                self.endpoint_url,
                data=bytes(body),
                headers={
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                    "User-Agent": "AgnesLipSync/1.0",
                },
                method="POST",
            )

            try:
                with urllib.request.urlopen(req, timeout=300) as resp:
                    with open(output_path, "wb") as out_f:
                        while True:
                            chunk = resp.read(65536)
                            if not chunk:
                                break
                            out_f.write(chunk)
                return output_path
            except urllib.error.URLError as e:
                logger.error(f"[LipSync] Service connection failed: {e}")
                raise LipSyncUnavailableError(f"LivePortrait service unavailable: {e}") from e
            except Exception as e:
                logger.error(f"[LipSync] Error during generation: {e}")
                raise LipSyncError(f"LivePortrait error: {e}") from e

        return await loop.run_in_executor(None, _do_request)


def create_lipsync_provider(endpoint_url: Optional[str] = None) -> BaseLipSyncProvider:
    """Фабрика для создания активного провайдера синхронизации губ."""
    return LivePortraitService(endpoint_url=endpoint_url)
