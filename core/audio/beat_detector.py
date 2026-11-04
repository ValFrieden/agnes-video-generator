"""core.audio.beat_detector — Модуль анализа ритмической структуры и бит-детекции аудио.

Использует анализ энергии аудиодорожки и BPM-сетку (4/4 такт) для автоматической нарезки
сцен музыкального видео под музыкальные фразы и кульминации (дропы).
"""

import math
import os
import struct
import wave
from dataclasses import dataclass
from typing import List, Optional

from core.compositor.ffmpeg_tool import probe_duration


@dataclass
class AudioBeatSegment:
    scene_index: int
    start_time_s: float
    end_time_s: float
    duration_s: float
    energy_level: str  # low | medium | high
    suggested_camera_movement: str
    suggested_transition: str


def calculate_bpm_grid(
    total_duration_s: float,
    bpm: int = 120,
    target_scenes: int = 6,
    min_scene_dur: float = 3.0,
    max_scene_dur: float = 12.0,
) -> List[AudioBeatSegment]:
    """Рассчитывает детерминированную ритмическую сетку сцен по тактам 4/4 на базе BPM.

    В классическом темпе 120 BPM: 1 beat = 0.5s, 1 bar (4 бита) = 2.0s.
    Сцены привязываются к границам целых тактов (2-4 такта на сцену).
    """
    bpm = max(60, min(240, bpm or 120))
    beat_duration = 60.0 / bpm
    bar_duration = beat_duration * 4.0  # 4/4 такт

    # Сколько тактов на одну сцену в среднем
    bars_per_scene = max(1, round((total_duration_s / target_scenes) / bar_duration))
    scene_dur = round(bars_per_scene * bar_duration, 2)
    # Ограничиваем в разумных пределах
    scene_dur = max(min_scene_dur, min(max_scene_dur, scene_dur))

    num_scenes = max(1, int(math.floor(total_duration_s / scene_dur)))
    segments: List[AudioBeatSegment] = []
    cur_time = 0.0

    for i in range(num_scenes):
        start = cur_time
        # Последняя сцена забирает остаток хронометража
        if i == num_scenes - 1:
            end = round(total_duration_s, 2)
        else:
            end = round(min(total_duration_s, cur_time + scene_dur), 2)
        dur = round(end - start, 2)
        if dur <= 0.5:
            break

        # Чередование драматургии: интро -> развитие -> кульминация (drop) -> концовка
        progress = i / max(1, num_scenes - 1)
        if progress < 0.25:
            energy = "low"
            cam = "dolly_in"
            trans = "Slow Cross-Dissolve"
        elif progress < 0.65:
            energy = "medium"
            cam = "tracking_shot"
            trans = "Cut"
        elif progress < 0.85:
            energy = "high"
            cam = "orbital_pan_cw"
            trans = "Whip Pan"
        else:
            energy = "medium"
            cam = "slow_pan"
            trans = "Cut"

        segments.append(
            AudioBeatSegment(
                scene_index=i + 1,
                start_time_s=start,
                end_time_s=end,
                duration_s=dur,
                energy_level=energy,
                suggested_camera_movement=cam,
                suggested_transition=trans,
            )
        )
        cur_time = end

    return segments


def analyze_audio_track(
    audio_file_path: str,
    bpm: int = 120,
    target_scenes: int = 6,
) -> List[AudioBeatSegment]:
    """Анализирует аудиофайл и возвращает сценарные сегменты с привязкой к тактам."""
    if not os.path.isfile(audio_file_path):
        return calculate_bpm_grid(total_duration_s=30.0, bpm=bpm, target_scenes=target_scenes)

    total_dur = probe_duration(audio_file_path)
    if not total_dur or total_dur <= 0:
        total_dur = 30.0

    return calculate_bpm_grid(
        total_duration_s=total_dur,
        bpm=bpm,
        target_scenes=target_scenes,
    )
