"""core.pipelines.music_video — Музыкальный видео-пайплайн (Audio-First MV Pipeline).

Разработан на базе опыта клипмейкинга SYNTX AI:
1. Аудиодорожка первична: ритмический анализ BPM и сетки тактов 4/4 через beat_detector.
2. Автоматическое распределение энергии (Low -> Medium -> High Climax / Drop).
3. Привязка 20 кинематографических пресетов движения камеры к энергетике трека.
4. Наложение оригинального трека на склеенный видеоряд.
"""

import asyncio
import logging
import os
import shutil
from typing import List, Optional

from core.api.image_providers import create_image_provider
from core.api.video_providers import create_video_provider
from core.audio.beat_detector import analyze_audio_track
from core.compositor.concatenator import VideoConcatenator
from core.config import DEFAULT_TEXT_MODEL
from core.pipelines import MultiScenePipeline
from core.screenwriter import Screenwriter
from core.screenwriter.camera_presets import apply_camera_movement_to_prompt
from core.screenwriter.scenes import ScreenwriterScenesMixin
from models.task import MusicVideoTask, SceneTask, StepStatus

logger = logging.getLogger(__name__)


class MusicVideoPipeline(MultiScenePipeline):
    """Audio-First пайплайн музыкального видеоклипа."""

    def __init__(
        self,
        api_key: str,
        task_id: str,
        dir_name: Optional[str] = None,
        chat_model: str = DEFAULT_TEXT_MODEL,
        image_model: str = "agnes-image-2.5-flash",
        video_model: str = "agnes-video-v2.0",
        progress_callback: Optional[callable] = None,
        shutdown_event: Optional[object] = None,
    ):
        super().__init__(
            api_key=api_key,
            task_id=task_id,
            dir_name=dir_name,
            progress_callback=progress_callback,
            shutdown_event=shutdown_event,
        )
        self.video_api = create_video_provider(
            api_key=api_key,
            default_model=video_model,
            shutdown_event=self.shutdown_event,
        )
        self.image_api = create_image_provider(api_key=api_key, model=image_model)
        self.screenwriter = Screenwriter(api_key=api_key, model=chat_model)
        self._state: Optional[MusicVideoTask] = None

    @property
    def state(self) -> Optional[MusicVideoTask]:
        return self._state

    # ==================================================================
    # MultiScenePipeline 抽象方法实现
    # ==================================================================

    async def _build_scenes(self) -> None:
        """Анализирует аудиодорожку по BPM и генерирует сцены под ритмическую сетку."""
        self._check_shutdown()
        state: MusicVideoTask = self._state

        audio_path = state.audio_file
        if not audio_path or not os.path.isfile(audio_path):
            audio_path = os.path.join(self.working_dir, "audio.mp3")

        bpm = state.bpm or 120
        target_scenes = max(2, state.scene_count or 6)

        logger.info(f"[MusicVideo] Analyzing audio track '{audio_path}' with BPM {bpm}...")
        segments = analyze_audio_track(audio_path, bpm=bpm, target_scenes=target_scenes)
        logger.info(f"[MusicVideo] Generated {len(segments)} beat-aligned scene segments.")

        scenes: List[SceneTask] = []
        durations: List[int] = []

        for seg in segments:
            dur_int = max(3, int(round(seg.duration_s)))
            durations.append(dur_int)

            # Базовое описание действия в зависимости от энергии
            if seg.energy_level == "high":
                action_text = f"High-energy cinematic climax, explosive visual motion, dynamic choreography under {state.visual_style}."
            elif seg.energy_level == "medium":
                action_text = f"Rhythmic progression, purposeful character movement through atmospheric lighting, {state.visual_style}."
            else:
                action_text = f"Intimate atmospheric introduction, gentle ambient drift, deep emotional contemplation, {state.visual_style}."

            # Накладываем пресет движения камеры
            prompt_with_cam = apply_camera_movement_to_prompt(action_text, seg.suggested_camera_movement)

            # Оборачиваем в посекундную 3-фазную структуру
            temporal_prompt = ScreenwriterScenesMixin.format_temporal_prompt_structure(
                raw_prompt=prompt_with_cam,
                duration_s=float(dur_int),
                camera_movement=seg.suggested_camera_movement,
            )

            st = SceneTask(
                index=seg.scene_index - 1,
                status=StepStatus.PENDING,
                scene_prompt=temporal_prompt,
                duration=dur_int,
            )
            scenes.append(st)

        state.scenes = scenes
        state.scene_count = len(scenes)
        state.scene_durations = durations
        self.task_manager.update_state(
            scene_count=len(scenes),
            scene_durations=durations,
            scenes=[s.model_dump() for s in scenes],
        )

    async def _build_reference_images(self) -> None:
        """Строит или валидирует референс-изображения для сцен."""
        self._check_shutdown()
        state: MusicVideoTask = self._state

        # Если пользователь предоставил эталонную картинку стиля/персонажа
        if state.reference_image and os.path.isfile(state.reference_image):
            logger.info(f"[MusicVideo] Using user provided reference image: {state.reference_image}")
            return

        # Иначе генерируем базовый референс стиля
        ref_path = os.path.join(self.working_dir, "style_ref.png")
        if os.path.isfile(ref_path):
            state.reference_image = ref_path
            return

        ref_prompt = f"Cinematic master still, {state.visual_style}, high aesthetic visual anchor, 8k resolution, dramatic lighting."
        try:
            image_provider = create_image_provider(self.api_key)
            await asyncio.to_thread(image_provider.generate_image, prompt=ref_prompt, output_file=ref_path)
            if os.path.isfile(ref_path):
                state.reference_image = ref_path
                self.task_manager.update_state(reference_image=ref_path)
                logger.info(f"[MusicVideo] Generated style reference image: {ref_path}")
        except Exception as e:
            logger.warning(f"[MusicVideo] Reference image generation failed, proceeding without anchor: {e}")

    def _get_scene_video_prompt(self, scene: SceneTask, index: int) -> str:
        """Возвращает посекундный промпт сцены."""
        return scene.scene_prompt

    def _get_scene_duration(self, scene: SceneTask, index: int) -> int:
        return scene.duration or 5

    def _get_scene_ref_images(self, scene: SceneTask, index: int) -> List[str]:
        state: MusicVideoTask = self._state
        if state.reference_image and os.path.isfile(state.reference_image):
            return [state.reference_image]
        return []

    async def _composite_final(self) -> str:
        """Склеивает сгенерированные видеофрагменты и накладывает оригинальный аудиоклип."""
        self._check_shutdown()
        state: MusicVideoTask = self._state
        scenes = state.scenes

        clip_paths = [s.video_file for s in scenes if s.video_file and os.path.isfile(s.video_file)]
        if not clip_paths:
            raise RuntimeError(f"No video clips generated for music video task {self.task_id}")

        final_output = os.path.join(self.working_dir, "final_video.mp4")
        concatenator = VideoConcatenator()
        audio_path = state.audio_file if (state.audio_file and os.path.isfile(state.audio_file)) else None

        if audio_path:
            logger.info(f"[MusicVideo] Concatenating {len(clip_paths)} clips with audio overlay {audio_path}...")
            await asyncio.to_thread(
                concatenator.concat_videos_with_audio_overlay,
                video_paths=clip_paths,
                audio_path=audio_path,
                srt_path=None,
                output_path=final_output,
            )
        else:
            logger.info(f"[MusicVideo] Concatenating {len(clip_paths)} silent clips...")
            await asyncio.to_thread(concatenator.concatenate, clip_paths, final_output)

        state.final_video_file = final_output
        self.task_manager.update_state(final_video_file=final_output)
        return final_output
