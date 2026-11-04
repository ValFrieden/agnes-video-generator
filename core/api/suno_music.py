"""core.api.suno_music — Suno AI Music Generation API Client & Preset Library.

Интегрирует генерацию музыки и фоновых аудиодорожек (BGM) через Suno AI (Kie.ai Cloud API).
Предоставляет:
1. SunoMusicAPI: асинхронный клиент для генерации треков (V6, V6_WILD, V6_MINI, V5, V4).
2. Каталог из 105 музыкальных стилей по 10 жанровым категориям.
3. Формирователь кинематографических музыкальных промптов (compose_music_prompt).
4. Автоматическое кэширование сгенерированных треков на локальный диск.
"""

import asyncio
import logging
import os
import re
import urllib.parse
from typing import Any, Callable, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# Провайдер по умолчанию
DEFAULT_KIE_API_BASE = "https://api.kie.ai"
DEFAULT_SUNO_MODEL = "V6"

# Каталог поддерживаемых моделей Suno AI
SUNO_MODELS: List[Dict[str, Any]] = [
    {
        "id": "V6",
        "name": "Suno V6 (Flagship Studio)",
        "badge": "★ Флагман / Flagship",
        "description": "Флагманская модель: максимальная чистота звука, естественная динамика инструментов и вокала, студийное сведение.",
        "max_lyrics_chars": 5000,
        "max_style_chars": 1000,
        "supports_negative_tags": True,
        "is_default": True,
        "tier": "flagship",
    },
    {
        "id": "V6_WILD",
        "name": "Suno V6 Wild (Creative Diversity)",
        "badge": "🔥 Wild / Разнообразие",
        "description": "Экспериментальная версия с максимальным разнообразием гармоний и неожиданными аранжировками.",
        "max_lyrics_chars": 5000,
        "max_style_chars": 1000,
        "supports_negative_tags": True,
        "is_default": False,
        "tier": "experimental",
    },
    {
        "id": "V6_MINI",
        "name": "Suno V6 Mini (Fast Draft)",
        "badge": "⚡ Mini / Скорость",
        "description": "Облегченная скоростная версия: сверхбыстрая генерация для драфтов и проверки ритма.",
        "max_lyrics_chars": 5000,
        "max_style_chars": 1000,
        "supports_negative_tags": True,
        "is_default": False,
        "tier": "fast",
    },
    {
        "id": "V5",
        "name": "Suno V5 (High Dynamic Range)",
        "badge": "V5 / Поколение 5",
        "description": "Модель 5-го поколения с широким динамическим диапазоном.",
        "max_lyrics_chars": 5000,
        "max_style_chars": 1000,
        "supports_negative_tags": False,
        "is_default": False,
        "tier": "standard",
    },
    {
        "id": "V4_5",
        "name": "Suno V4.5 (Enhanced Studio)",
        "badge": "V4.5 Studio",
        "description": "Доработанная версия 4-го поколения с улучшенным балансом инструментов.",
        "max_lyrics_chars": 4000,
        "max_style_chars": 500,
        "supports_negative_tags": False,
        "is_default": False,
        "tier": "standard",
    },
    {
        "id": "V4",
        "name": "Suno V4 (Studio Fidelity)",
        "badge": "V4 Классика",
        "description": "Классическая студийная модель 4-й версии с высокой разборчивостью.",
        "max_lyrics_chars": 3000,
        "max_style_chars": 200,
        "supports_negative_tags": False,
        "is_default": False,
        "tier": "legacy",
    },
]

# Библиотека стилей по 10 категориям (105 стилей)
MUSIC_STYLE_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "cinematic": {
        "title": "Саундтреки & Кинематограф (Soundtracks)",
        "styles": [
            {"name": "Epic Orchestral Trailer", "bpm": 120, "key": "D Minor", "instruments": "heavy brass, cinematic strings, taiko drums, sub drops"},
            {"name": "Nordic Viking War Chant", "bpm": 95, "key": "A Minor", "instruments": "tagelharpa, war horn, throat singing, deep ambient drums"},
            {"name": "Dark Ambient Cyberpunk", "bpm": 105, "key": "C Minor", "instruments": "sub bass, industrial metallic drone, analog synthesizer"},
            {"name": "Emotional Piano & Cello", "bpm": 75, "key": "E Minor", "instruments": "warm upright piano, solo cello, soft atmospheric pads"},
            {"name": "Sci-Fi Space Odyssey", "bpm": 85, "key": "F Minor", "instruments": "vangelis synth brass, celestial choir, analog arpeggio"},
            {"name": "Fantasy Medieval Tavern", "bpm": 115, "key": "G Major", "instruments": "lute, wooden flute, bodhran, tambourine"},
            {"name": "Gothic Orchestral Horror", "bpm": 80, "key": "C Minor", "instruments": "pipe organ, discordant strings, ominous choir, bell chimes"},
            {"name": "Neo-Western Ennio Morricone", "bpm": 100, "key": "D Minor", "instruments": "whistling, acoustic nylon guitar, trumpet, twangy electric guitar"},
            {"name": "Action Chase Hybrid Orchestral", "bpm": 140, "key": "B Minor", "instruments": "staccato violins, 808 sub, aggressive synth bass, breakbeats"},
            {"name": "Zen Meditation Asian Ambient", "bpm": 65, "key": "D Major", "instruments": "koto, shakuhachi flute, singing bowls, temple bells"},
        ],
    },
    "synthwave": {
        "title": "Электроника & Синтвейв (Electronic & Synth)",
        "styles": [
            {"name": "80s Outrun Synthwave", "bpm": 120, "key": "C Minor", "instruments": "analog synth bass, gated reverb snare, neon arpeggiator, lead synth"},
            {"name": "Darksynth Cyberpunk 2077", "bpm": 130, "key": "F Minor", "instruments": "distorted saw bass, glitch percussion, aggressive dark pads"},
            {"name": "Retrowave Chillwave", "bpm": 95, "key": "A Major", "instruments": "vintage chorus pads, sidechain pads, dreamy synth lead"},
            {"name": "Melodic Progressive House", "bpm": 126, "key": "G Minor", "instruments": "plucked lead, four-on-the-floor kick, atmospheric vocal chops"},
            {"name": "Industrial EBM / Dark Techno", "bpm": 135, "key": "D Minor", "instruments": "heavy 909 kick, acid 303 bassline, metallic percussion"},
            {"name": "Future Garage & Chillstep", "bpm": 130, "key": "E Minor", "instruments": "syncopated 2-step beat, warm reese bass, vinyl crackle"},
            {"name": "Deep Minimal Techno", "bpm": 124, "key": "A Minor", "instruments": "hypnotic sub bass, crisp hi-hats, subtle modular clicks"},
            {"name": "Electro Swing 1920s", "bpm": 125, "key": "C Major", "instruments": "swing brass, vintage clarinet, modern punchy kick, gramophone filter"},
            {"name": "Synth-Pop 80s Revival", "bpm": 118, "key": "F Major", "instruments": "juno-106 keys, LinnDrum, funky synth bass, catchy hook"},
            {"name": "Liquid Drum and Bass", "bpm": 174, "key": "E Minor", "instruments": "fast rolling breakbeat, deep sub bass, soulful rhodes piano"},
        ],
    },
    "rock": {
        "title": "Рок & Метал (Rock & Metal)",
        "styles": [
            {"name": "Classic 70s Hard Rock", "bpm": 125, "key": "E Minor", "instruments": "overdriven Gibson Les Paul, punchy drums, driving bass"},
            {"name": "Grunge & 90s Alternative", "bpm": 110, "key": "D Minor", "instruments": "fuzzy distorted guitars, energetic drum fills, raw bass"},
            {"name": "Post-Rock Ambient Crescendo", "bpm": 85, "key": "G Major", "instruments": "shimmer reverb guitars, bowing cymbals, swelling tom drums"},
            {"name": "Modern Djent & Progressive Metal", "bpm": 130, "key": "Drop A", "instruments": "8-string palm-muted guitars, polymetric double-kick, tight snares"},
            {"name": "Indie Pop-Rock", "bpm": 120, "key": "A Major", "instruments": "jangly telecaster, driving four-on-the-floor beat, melodic bass"},
            {"name": "Symphonic Power Metal", "bpm": 150, "key": "D Minor", "instruments": "twin lead guitars, orchestral choir, blazing double-bass drums"},
            {"name": "Punk Rock Fast Energy", "bpm": 165, "key": "E Major", "instruments": "fast power chords, thrashing cymbals, upfront bassline"},
            {"name": "Southern Blues Rock", "bpm": 95, "key": "A Minor", "instruments": "slide resonator guitar, hammond organ, stomping kick drum"},
            {"name": "Stoner & Desert Rock", "bpm": 88, "key": "C Minor", "instruments": "heavy fuzz bass, downtuned riffs, slow heavy groove"},
            {"name": "Math Rock Midwest Emo", "bpm": 135, "key": "F# Major", "instruments": "clean tapping guitars, odd meter drums, vibrant dynamics"},
        ],
    },
    "hiphop": {
        "title": "Хип-хоп, Трэп & Фонк (Hip-Hop & Phonk)",
        "styles": [
            {"name": "Drift Phonk Cowbell", "bpm": 145, "key": "F Minor", "instruments": "distorted 808 bass, memphis rap vocal chops, aggressive cowbell melody"},
            {"name": "Lo-Fi Study Hip-Hop", "bpm": 82, "key": "Eb Major", "instruments": "dusty rhodes chords, vinyl crackle, mellow boom-bap drums, jazz flute"},
            {"name": "Boom-Bap Golden Era 90s", "bpm": 92, "key": "C Minor", "instruments": "sampled vinyl horns, crunchy snare, acoustic upright bass"},
            {"name": "Dark Trap Cinematic 808", "bpm": 135, "key": "C# Minor", "instruments": "rolling hi-hats, sub-shaking 808 bass, bell pluck melody"},
            {"name": "Chillhop Sunday Morning", "bpm": 78, "key": "Ab Major", "instruments": "lo-fi acoustic guitar, soft shaker, sub bass, birdsong ambiance"},
            {"name": "UK Drill Syncopated", "bpm": 142, "key": "D Minor", "instruments": "sliding 808s, ghost snares, dark detuned piano"},
            {"name": "Jazz-Rap A Tribe Called Quest", "bpm": 90, "key": "F Minor", "instruments": "upright jazz bass, brass stabs, warm Rhodes piano, swing hi-hats"},
            {"name": "Brazilian Phonk Baile Funk", "bpm": 130, "key": "G Minor", "instruments": "heavy tamborzao beat, aggressive brass stabs, 808 glide"},
            {"name": "Cloud Rap Atmospheric", "bpm": 120, "key": "Bb Minor", "instruments": "ethereal synth pads, vocal echoes, slow 808 beat"},
            {"name": "East Coast Gritty Rap Beat", "bpm": 88, "key": "A Minor", "instruments": "grimy piano loops, raw vinyl kick, menacing strings"},
        ],
    },
    "acoustic": {
        "title": "Акустика & Эмбиент (Acoustic & Ambient)",
        "styles": [
            {"name": "Warm Coffeehouse Acoustic", "bpm": 88, "key": "C Major", "instruments": "fingerpicked steel-string acoustic guitar, soft shaker, subtle upright bass"},
            {"name": "Deep Healing 432 Hz Solfeggio", "bpm": 60, "key": "F Major", "instruments": "crystalline pads, tibetan singing bowls, warm drone, 432Hz tuning"},
            {"name": "Lofi Bedroom Ukulele", "bpm": 80, "key": "G Major", "instruments": "gentle ukulele strum, tape flutter, soft handclaps, warm room tone"},
            {"name": "Celtic Harp & Misty Woods", "bpm": 75, "key": "D Minor", "instruments": "celtic harp, penny whistle, gentle bodhran, wind ambient sound"},
            {"name": "Spanish Flamenco Classical", "bpm": 110, "key": "A Phrygian", "instruments": "nylon guitar rasgueado, cajon percussion, palmas claps"},
            {"name": "Sleep Ambient Binaural Delta", "bpm": 50, "key": "C Major", "instruments": "low sine drones, theta binaural waves, warm analog synth swells"},
            {"name": "Rainy Window Piano Solo", "bpm": 70, "key": "Ab Major", "instruments": "felt piano, natural rain sound, distant thunder rumble"},
            {"name": "Mountain Folk Banjo & Fiddle", "bpm": 130, "key": "G Major", "instruments": "clawhammer banjo, bluegrass fiddle, acoustic dreadnought guitar"},
            {"name": "Ambient Space Drone", "bpm": 55, "key": "D Minor", "instruments": "granular synth clouds, infinite delay guitar, cosmic sub frequency"},
            {"name": "Acoustic Campfire Serenade", "bpm": 95, "key": "D Major", "instruments": "strummed Martin acoustic, harmonica, campfire crackle, soft tambourine"},
        ],
    },
    "pop": {
        "title": "Поп & Радио-Хиты (Pop & Retro)",
        "styles": [
            {"name": "Modern Dance-Pop Anthem", "bpm": 124, "key": "A Minor", "instruments": "punchy modern kick, sidechained saw chords, melodic vocal chops"},
            {"name": "Disco Funk 70s Studio 54", "bpm": 118, "key": "D Minor", "instruments": "slap bass, wah-wah guitar, brass horn section, four-on-floor disco drums"},
            {"name": "K-Pop High Energy Beat", "bpm": 132, "key": "F# Minor", "instruments": "trap-infused pop beat, bright synth brass, pitched percussion"},
            {"name": "Afro-Pop Sunshine Grooves", "bpm": 105, "key": "C Major", "instruments": "log drum, electric guitar riffs, congas, warm synth pads"},
            {"name": "Acoustic Pop Ballad", "bpm": 78, "key": "G Major", "instruments": "grand piano, lush string orchestra, gentle acoustic guitar"},
        ],
    },
}


def compose_music_prompt(
    genre: str = "Cinematic Soundtrack",
    instruments: str = "cinematic strings, brass, taiko drums",
    bpm: int = 120,
    key_signature: str = "C Minor",
    vocal_profile: Optional[str] = None,
    mood: Optional[str] = "Epic",
    resonance_hz: int = 432,
) -> str:
    """Формирует калиброванный промпт стиля для Suno AI.

    Синтезирует сбалансированную формулу звучания, темпа и инструментов.
    """
    parts = [genre.strip()]
    if mood:
        parts.append(f"{mood.strip()} atmosphere")
    if instruments:
        parts.append(instruments.strip())
    if bpm > 0:
        parts.append(f"{bpm} BPM")
    if key_signature:
        parts.append(key_signature.strip())
    if vocal_profile:
        parts.append(vocal_profile.strip())
    else:
        parts.append("instrumental, audiophile master")
    if resonance_hz in [432, 528]:
        parts.append(f"{resonance_hz} Hz harmonic resonance")
    return ", ".join(parts)


def get_preset_by_name(style_name: str) -> Optional[Dict[str, Any]]:
    """Находит пресет по названию во всех категориях."""
    s_clean = style_name.strip().lower()
    for cat_data in MUSIC_STYLE_CATEGORIES.values():
        for st in cat_data["styles"]:
            if st["name"].lower() == s_clean or s_clean in st["name"].lower():
                return st
    return None


class SunoMusicAPI:
    """Асинхронный клиент для взаимодействия с Suno AI через Kie.ai Cloud API."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("KIE_API_KEY") or os.getenv("SUNO_API_KEY") or ""
        self.base_url = (base_url or os.getenv("KIE_API_BASE") or DEFAULT_KIE_API_BASE).rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def is_configured(self) -> bool:
        """Проверяет, задан ли API-ключ для музыкального генератора."""
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    async def get_credit(self) -> float:
        """Запрашивает текущий баланс кредитов провайдера Kie.ai."""
        if not self.is_configured():
            raise ValueError("KIE_API_KEY / SUNO_API_KEY не сконфигурирован.")

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{self.base_url}/api/v1/chat/credit", headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") == 200:
                return float(data.get("data", 0.0))
            raise ValueError(f"Ошибка получения баланса: {data.get('msg', 'Unknown error')}")

    async def generate_music(
        self,
        prompt: str,
        style: Optional[str] = None,
        title: Optional[str] = "Cinematic BGM",
        custom_mode: bool = True,
        instrumental: bool = True,
        model: str = DEFAULT_SUNO_MODEL,
        vocal_gender: Optional[str] = None,
        negative_tags: Optional[str] = None,
        audio_id: Optional[str] = None,
        continue_at: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Отправляет задачу генерации трека в Suno AI (Kie.ai).

        Args:
            prompt: Описание трека или текст куплетов (если custom_mode=True).
            style: Промпт стиля (жанр, BPM, инструменты).
            title: Название трека.
            custom_mode: Использовать ли точные настройки стиля и текста.
            instrumental: True для инструментальной дорожки (BGM), False для вокала.
            model: Модель (V6, V6_WILD, V6_MINI, V5, V4_5, V4).
            vocal_gender: Пол вокала ('m' или 'f') при instrumental=False.
            negative_tags: Нежелательные стили / инструменты.
            audio_id: ID исходного аудио для продолжения.
            continue_at: Временная отметка для продолжения трека.

        Returns:
            Словарь с taskId задачи в Kie.ai.
        """
        if not self.is_configured():
            raise ValueError(
                "Suno API Key не сконфигурирован! Установите KIE_API_KEY или SUNO_API_KEY в окружении."
            )

        payload: Dict[str, Any] = {
            "prompt": prompt,
            "customMode": custom_mode,
            "instrumental": instrumental,
            "model": model,
        }
        if style:
            payload["style"] = style
        if title:
            payload["title"] = title
        if negative_tags:
            payload["negativeTags"] = negative_tags
        if vocal_gender and vocal_gender.lower() in ["m", "f"]:
            payload["vocalGender"] = vocal_gender.lower()
        if audio_id:
            payload["audio_id"] = audio_id
        if continue_at is not None and continue_at >= 0:
            payload["continue_at"] = continue_at

        logger.info(
            f"[SunoMusic] Dispatching generation: title='{title}', model='{model}', "
            f"instrumental={instrumental}, style='{style}'"
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.base_url}/api/v1/generate", json=payload, headers=self.headers)

            # Резервный эндпоинт jobs/createTask при 404
            if resp.status_code == 404:
                task_payload = {"model": "ai-music-api/generate", "input": payload}
                resp = await client.post(f"{self.base_url}/api/v1/jobs/createTask", json=task_payload, headers=self.headers)

            resp.raise_for_status()
            res_json = resp.json()
            if res_json.get("code") == 200:
                return res_json.get("data", {})
            raise ValueError(f"Suno API Error: {res_json.get('msg', 'Unknown error')}")

    async def get_record_info(self, task_id: str) -> Dict[str, Any]:
        """Получает текущий статус выполнения задачи по task_id."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            url = f"{self.base_url}/api/v1/record/info?taskId={task_id}"
            resp = await client.get(url, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") == 200:
                return data.get("data", {})
            return data

    async def download_file(self, url: str, dest_path: str) -> str:
        """Скачивает аудиофайл по URL и сохраняет на локальный диск."""
        os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            async with client.stream("GET", url) as resp:
                resp.raise_for_status()
                with open(dest_path, "wb") as f:
                    async for chunk in resp.aiter_bytes(chunk_size=16384):
                        f.write(chunk)
        logger.info(f"[SunoMusic] Successfully cached audio to {dest_path}")
        return dest_path

    async def poll_and_download(
        self,
        task_id: str,
        dest_path: str,
        max_attempts: int = 60,
        delay_sec: float = 6.0,
        progress_cb: Optional[Callable[[str, float], None]] = None,
    ) -> Dict[str, Any]:
        """Опрашивает статус задачи до завершения и скачивает трек локально."""
        logger.info(f"[SunoMusic] Polling task {task_id} up to {max_attempts * delay_sec}s...")
        for attempt in range(max_attempts):
            await asyncio.sleep(delay_sec)
            try:
                info = await self.get_record_info(task_id)
                raw_state = info.get("state") or info.get("status") or ""
                state = str(raw_state).lower()
                success_flag = info.get("successFlag")
                response = info.get("response") or {}

                if isinstance(response, str):
                    import json
                    try:
                        response = json.loads(response)
                    except Exception:
                        pass

                error_code = info.get("errorCode")
                has_error = (
                    error_code is not None
                    and error_code != 0
                    and error_code != ""
                    and error_code != "0"
                )

                is_success = (state in ["success", "completed", "finish"]) or (success_flag == 1)
                is_fail = (state in ["fail", "failed", "error"]) or (success_flag == 2) or has_error

                if progress_cb:
                    progress_pct = min(0.95, (attempt + 1) / max_attempts)
                    progress_cb(f"Suno generating ({state or 'processing'})...", progress_pct)

                if is_success:
                    # Извлекаем аудио URL
                    suno_data = response.get("sunoData") or response.get("data") or []
                    audio_url = None
                    duration = 0.0
                    title = "Generated Music"

                    if isinstance(suno_data, list) and len(suno_data) > 0:
                        first_item = suno_data[0]
                        audio_url = (
                            first_item.get("audioUrl")
                            or first_item.get("streamAudioUrl")
                            or first_item.get("url")
                        )
                        duration = float(first_item.get("duration", 0) or 0)
                        title = first_item.get("title") or title
                    else:
                        audio_url = (
                            response.get("resultAudioUrl")
                            or response.get("audio_url")
                            or response.get("audioUrl")
                        )
                        duration = float(response.get("duration", 0) or 0)

                    if not audio_url:
                        raise ValueError(f"Task {task_id} completed, but no audio URL found in {response}")

                    # Скачиваем на локальный диск
                    local_file = await self.download_file(audio_url, dest_path)
                    logger.info(f"[SunoMusic] Task {task_id} ready! Saved to {local_file} ({duration:.1f}s)")
                    return {
                        "status": "success",
                        "audio_url": audio_url,
                        "local_path": local_file,
                        "duration": duration,
                        "title": title,
                        "task_id": task_id,
                    }

                elif is_fail:
                    err_msg = info.get("errorMessage") or info.get("msg") or "Music generation failed"
                    logger.error(f"[SunoMusic] Task {task_id} failed: {err_msg}")
                    raise RuntimeError(f"Suno AI generation failed: {err_msg}")

            except Exception as e:
                if "Suno AI generation failed" in str(e):
                    raise
                logger.warning(f"[SunoMusic] Poll attempt {attempt + 1} warning: {e}")

        raise TimeoutError(f"Suno generation timed out for task {task_id}")
