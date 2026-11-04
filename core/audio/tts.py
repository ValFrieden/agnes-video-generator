"""core.audio.tts — TTS 统一接口：EdgeTTSEngine + SilentTTSEngine

基于 edge_tts（免费 Azure Edge TTS）和静音占位两种实现。
"""

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from typing import Optional, Tuple

import edge_tts

from core.async_io import async_open
from core.compositor.ffmpeg_tool import resolve_binary
from core.i18n_backend import translate

logger = logging.getLogger(__name__)


class TTSEngine(ABC):
    """TTS 抽象基类。"""

    @abstractmethod
    async def generate(
        self, text: str, output_path: str, voice: str = "zh-CN-XiaoxiaoNeural", rate: str = "+0%"
    ) -> Tuple[str, object]:
        """生成音频文件，返回 (audio_path, sub_maker_or_cues)。"""
        ...


class EdgeTTSEngine(TTSEngine):
    """基于 edge_tts 的免费 TTS 引擎。

    generate() 返回 (audio_path, sub_maker)，其中 sub_maker 是 edge_tts.SubMaker 实例，
    包含逐词时间戳 cues，可用于生成 SRT 字幕。
    """

    async def generate(
        self, text: str, output_path: str, voice: str = "zh-CN-XiaoxiaoNeural", rate: str = "+0%"
    ) -> Tuple[str, "edge_tts.SubMaker"]:
        """生成 TTS 音频 + SubMaker（含 cues 时间戳）。

        Args:
            text: 要朗读的文本
            output_path: 输出音频文件路径（.mp3）
            voice: edge_tts 语音角色
            rate: 语速调节（如 "+0%", "+20%", "-10%"）

        Returns:
            (audio_path, sub_maker) 元组

        Raises:
            RuntimeError: TTS 生成失败时抛出，调用方应降级到 SilentTTSEngine。
        """
        logger.info(f"[TTS] Generating audio: voice={voice}, rate={rate}, text={len(text)} chars...")

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
                sub_maker = edge_tts.SubMaker()

                tmp_path = output_path + ".tmp"
                async with await async_open(tmp_path, "wb") as audio_file:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            await audio_file.write(chunk["data"])
                        elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                            sub_maker.feed(chunk)

                # 原子替换，避免半成品被误用
                os.replace(tmp_path, output_path)
                logger.info(f"[TTS] Audio saved: {output_path}")
                return output_path, sub_maker
            except Exception as e:
                # 清理半成品文件
                for p in (tmp_path, output_path):
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                        except OSError:
                            pass
                if attempt < max_attempts - 1:
                    logger.warning(f"[TTS] edge_tts attempt {attempt + 1}/{max_attempts} failed: {e}, retrying...")
                    await asyncio.sleep(3)
                    continue
                logger.error(f"[TTS] edge_tts failed after {max_attempts} attempts: {e}")
                raise RuntimeError(f"EdgeTTS generation failed: {e}") from e

    async def harvest_cues(
        self, text: str, voice: str = "zh-CN-XiaoxiaoNeural", rate: str = "+0%"
    ) -> "edge_tts.SubMaker":
        """仅采集逐词时间戳，不生成/不落盘音频字节（路径 B：音频关、字幕开）。

        edge_tts 的 WordBoundary 与音频数据交织于同一 stream，需消费完整 stream
        才能收齐全部 cues；本方法只把 WordBoundary/SentenceBoundary 喂给 SubMaker，
        音频数据直接丢弃。返回含 .cues 的 sub_maker，供 generate_cue_aware_srt 使用。

        字幕只需时间线真值，不需音频字节——这正是「cues 采集」与「音频输出」解耦的核心。

        Args:
            text: 要朗读的文本
            voice: edge_tts 语音角色
            rate: 语速调节

        Returns:
            含逐词 cues 的 edge_tts.SubMaker 实例

        Raises:
            RuntimeError: 采集失败时抛出，调用方应降级到 SilentTTSEngine（字幕回退 legacy）。
        """
        logger.info(
            f"[TTS] Harvesting cues only: voice={voice}, rate={rate}, text={len(text)} chars..."
        )

        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
                sub_maker = edge_tts.SubMaker()
                async for chunk in communicate.stream():
                    if chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                        sub_maker.feed(chunk)
                cue_count = len(getattr(sub_maker, "cues", []) or [])
                logger.info(f"[TTS] Cues harvested: {cue_count} cues")
                return sub_maker
            except Exception as e:
                if attempt < max_attempts - 1:
                    logger.warning(
                        f"[TTS] harvest_cues attempt {attempt + 1}/{max_attempts} "
                        f"failed: {e}, retrying..."
                    )
                    await asyncio.sleep(3)
                    continue
                logger.error(f"[TTS] harvest_cues failed after {max_attempts} attempts: {e}")
                raise RuntimeError(f"EdgeTTS cue harvest failed: {e}") from e


class SilentTTSEngine(TTSEngine):
    """静音占位 TTS 引擎。

    生成指定时长的静音音频，返回空 cues。用于用户关闭旁白时仍需要字幕时间轴的场景。
    """

    async def generate(
        self,
        text: str,
        output_path: str,
        voice: str = "zh-CN-XiaoxiaoNeural",
        rate: str = "+0%",
        duration_sec: Optional[float] = None,
    ) -> Tuple[str, dict]:
        """生成静音音频。

        Args:
            text: 文本（用于估算时长，如果 duration_sec 未提供）
            output_path: 输出音频文件路径
            voice: 忽略（静音模式）
            rate: 忽略（静音模式）
            duration_sec: 指定静音时长（秒），如果不提供则按文本长度估算

        Returns:
            (audio_path, empty_cues_dict) 元组
        """
        if duration_sec is None:
            # 估算时长：中文 4 字/秒
            duration_sec = max(len(text) / 4.0, 1.0)

        logger.info(f"[TTS] Generating silent audio: {duration_sec:.1f}s → {output_path}")

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        # 统一解析 ffmpeg 路径（Issue #78）：裸 "ffmpeg" 在无系统 ffmpeg 的
        # Windows 上会让 CreateProcess 抛 [WinError 2]，且错误信息完全不可读
        ffmpeg = resolve_binary("ffmpeg")
        if not ffmpeg:
            raise RuntimeError(translate("error.ffmpeg_missing"))

        # 使用 ffmpeg 生成静音音频
        proc = await asyncio.create_subprocess_exec(
            ffmpeg, "-y",
            "-f", "lavfi",
            "-i", "anullsrc=r=44100:cl=mono",
            "-t", str(duration_sec),
            "-c:a", "libmp3lame",
            "-q:a", "4",
            output_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()

        # P9: 检查 ffmpeg 返回码，失败时抛出异常而非静默返回
        if proc.returncode != 0:
            err_msg = stderr.decode(errors="replace")[:500] if stderr else ""
            raise RuntimeError(
                f"[TTS] ffmpeg silent generation failed (code {proc.returncode}): {err_msg}"
            )

        # 返回空 cues（用 None 而非 {}，让下游正确识别为无 SubMaker 可用）
        return output_path, None


class KokoroTTSEngine(TTSEngine):
    """基于 Kokoro-82M (hexgrad) 的开源本地轻量级 TTS 引擎 (Apache 2.0)。

    无需外部 API Key，完全在本地 CPU/GPU 离线运行，高保真 24kHz 音质。
    若未安装依赖或模型尚未就绪，提供 is_available() 状态自检，并在失败时优雅抛出 RuntimeError
    以便流水线自动回退。
    """

    VOICE_LANG_PREFIX = {
        "a": "a",  # American English (e.g. af_heart, am_adam)
        "b": "b",  # British English (e.g. bf_emma, bm_george)
        "e": "e",  # Spanish (e.g. ef_dora, em_alex)
        "f": "f",  # French (e.g. ff_siwis)
        "h": "h",  # Hindi
        "i": "i",  # Italian
        "j": "j",  # Japanese
        "p": "p",  # Brazilian Portuguese
        "z": "z",  # Mandarin Chinese (e.g. zf_xiaobei, zm_yunjian)
    }

    def __init__(self, lang_code: str = "a"):
        """初始化 Kokoro 引擎。
        
        Args:
            lang_code: 默认语言代码 ('a'=American English, 'b'=British, 'z'=Chinese 等)
        """
        self._default_lang = lang_code
        self._pipeline = None

    @classmethod
    def is_available(cls) -> bool:
        """检查本地环境是否满足 Kokoro 运行所需依赖。"""
        try:
            import kokoro  # noqa: F401
            import soundfile  # noqa: F401
            return True
        except ImportError:
            return False

    def _infer_lang_code(self, voice: str) -> str:
        """根据音色名称前缀（如 af_heart -> a, zf_xiaobei -> z）推断语言代码。"""
        if voice and len(voice) >= 2 and voice[0] in self.VOICE_LANG_PREFIX:
            return voice[0]
        return self._default_lang

    def _parse_speed(self, rate: str) -> float:
        """将 rate 字符串（如 '+0%', '+20%', '-10%'）转换为浮点倍速（如 1.0, 1.2, 0.9）。"""
        if not rate:
            return 1.0
        try:
            cleaned = rate.replace("%", "").strip()
            if cleaned.startswith("+"):
                percent = float(cleaned[1:])
                return round(1.0 + percent / 100.0, 2)
            elif cleaned.startswith("-"):
                percent = float(cleaned[1:])
                return round(max(0.5, 1.0 - percent / 100.0), 2)
            else:
                return float(cleaned)
        except Exception:
            return 1.0

    async def generate(
        self, text: str, output_path: str, voice: str = "af_heart", rate: str = "+0%"
    ) -> Tuple[str, Optional[object]]:
        """使用本地 Kokoro-82M 生成音频文件 (.mp3 或 .wav)。

        Args:
            text: 要朗读的文本
            output_path: 输出音频文件路径
            voice: Kokoro 音色标识（默认 af_heart）
            rate: 语速调节（如 "+0%", "+20%"）

        Returns:
            (audio_path, None) 元组

        Raises:
            RuntimeError: 当依赖未安装或推理失败时抛出。
        """
        if not self.is_available():
            raise RuntimeError(
                "[TTS] Kokoro-82M 依赖未安装。如需启用离线合成，请运行: pip install kokoro soundfile"
            )

        logger.info(f"[TTS] [Kokoro] Generating audio: voice={voice}, rate={rate}, text={len(text)} chars...")
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        lang_code = self._infer_lang_code(voice)
        speed = self._parse_speed(rate)
        loop = asyncio.get_event_loop()

        def _synthesize() -> str:
            import numpy as np
            import soundfile as sf
            from kokoro import KPipeline

            pipeline = KPipeline(lang_code=lang_code)
            generator = pipeline(text, voice=voice, speed=speed, split_pattern=r"\n+")
            
            all_audio = []
            for _, _, audio in generator:
                if audio is not None and len(audio) > 0:
                    all_audio.append(audio)

            if not all_audio:
                raise RuntimeError("[TTS] Kokoro did not produce any audio segments")

            combined_audio = np.concatenate(all_audio) if len(all_audio) > 1 else all_audio[0]

            # 统一输出 WAV 或 MP3
            is_mp3 = output_path.lower().endswith(".mp3")
            temp_wav = output_path + ".wav" if is_mp3 else output_path
            sf.write(temp_wav, combined_audio, 24000)

            if is_mp3:
                ffmpeg = resolve_binary("ffmpeg") or "ffmpeg"
                import subprocess
                cmd = [
                    ffmpeg, "-y",
                    "-i", temp_wav,
                    "-c:a", "libmp3lame",
                    "-q:a", "2",
                    output_path
                ]
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                try:
                    if os.path.exists(temp_wav):
                        os.remove(temp_wav)
                except OSError:
                    pass
                if res.returncode != 0:
                    raise RuntimeError(f"[TTS] Failed to convert Kokoro wav to mp3: {res.stderr.decode()[:300]}")

            return output_path

        await loop.run_in_executor(None, _synthesize)
        logger.info(f"[TTS] [Kokoro] Audio successfully generated: {output_path}")
        return output_path, None



class WhisperSubtitleEngine:
    """Verfeinert Untertitel-Timestamps durch lokale Whisper-Transkription.

    Kein TTS — transkribiert bereits vorhandene Audiodateien und liefert
    wortgenaue Timestamps als SRT-kompatible Cues zurück.
    Nutzt openai-whisper (lokal, kein API-Key nötig).

    Modellgrößen (trade-off Geschwindigkeit/Genauigkeit):
        "tiny"   — sehr schnell, grobe Timestamps
        "base"   — empfohlen: guter Kompromiss (Standard)
        "small"  — besser für schwierige Akzente / Musik-TTS
        "medium" — hohe Genauigkeit, langsam auf CPU
        "large"  — maximale Genauigkeit, nur GPU empfohlen

    Verwendung:
        engine = WhisperSubtitleEngine(model_name="base")
        cues = await engine.transcribe("narration.mp3", language="ru")
        # cues: List[dict] mit keys: word (str), start (float), end (float)
    """

    def __init__(self, model_name: str = "base"):
        """Initialisiert den Engine (Modell wird lazy geladen).

        Args:
            model_name: Whisper-Modellgröße: "tiny", "base", "small", "medium", "large".
        """
        self._model_name = model_name
        self._model = None  # lazy load

    def _load_model(self):
        """Lädt Whisper-Modell (lazy, erster Aufruf dauert ~5-30s je nach Modell)."""
        if self._model is None:
            try:
                import whisper
                logger.info(f"[TTS] Lade Whisper-Modell: '{self._model_name}'")
                self._model = whisper.load_model(self._model_name)
                logger.info(f"[TTS] Whisper-Modell '{self._model_name}' geladen ✅")
            except ImportError:
                raise RuntimeError(
                    "[TTS] openai-whisper nicht installiert. "
                    "Installieren mit: pip install openai-whisper"
                )

    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        word_timestamps: bool = True,
    ) -> list:
        """Transkribiert Audio und gibt Wort-Timestamps zurück.

        Args:
            audio_path: Pfad zur Audiodatei (.mp3, .wav, .ogg etc.)
            language: Sprachcode (z.B. "ru", "de", "zh", None = auto-detect).
                      Automatische Erkennung verlangsamt den ersten Durchlauf.
            word_timestamps: True = Wort-Level; False = Segment-Level Timestamps.

        Returns:
            Liste von Dicts: [{"word": str, "start": float, "end": float}, ...]
            Leere Liste bei leerem Audio oder fehlgeschlagener Transkription.

        Raises:
            RuntimeError: Wenn openai-whisper nicht verfügbar ist.
            FileNotFoundError: Wenn audio_path nicht existiert.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"[TTS] Audio nicht gefunden: {audio_path}")

        self._load_model()
        loop = asyncio.get_event_loop()

        def _do_transcribe() -> list:
            logger.info(
                f"[TTS] Whisper transkribiert: {os.path.basename(audio_path)}"
                f" (lang={language or 'auto'}, word_ts={word_timestamps})"
            )
            options: dict = {"word_timestamps": word_timestamps}
            if language:
                options["language"] = language

            result = self._model.transcribe(audio_path, **options)

            cues = []
            if word_timestamps:
                for segment in result.get("segments", []):
                    for word_info in segment.get("words", []):
                        cues.append({
                            "word": word_info.get("word", "").strip(),
                            "start": float(word_info.get("start", 0.0)),
                            "end": float(word_info.get("end", 0.0)),
                        })
            else:
                # Segment-Level Fallback
                for segment in result.get("segments", []):
                    cues.append({
                        "word": segment.get("text", "").strip(),
                        "start": float(segment.get("start", 0.0)),
                        "end": float(segment.get("end", 0.0)),
                    })

            logger.info(f"[TTS] Whisper: {len(cues)} Cues extrahiert")
            return cues

        return await loop.run_in_executor(None, _do_transcribe)
