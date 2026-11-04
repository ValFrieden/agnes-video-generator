"""core.compositor.processor — 视频处理器

提供缩放、帧提取、静音音频生成、尾帧冻结等工具方法。
"""

import logging
import os

from typing import Optional, Dict, List

from core.compositor.ffmpeg_tool import resolve_binary

logger = logging.getLogger(__name__)


class VideoProcessor:
    """视频处理工具集（缩放、帧提取、静音生成、尾帧冻结）。"""

    @staticmethod
    def resize_video(input_path: str, width: int, height: int, output_path: str) -> str:
        """缩放视频到指定分辨率。"""
        logger.info(f"[Compositor] Resizing: {input_path} → {width}x{height}")
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        import subprocess
        subprocess.run([
            resolve_binary("ffmpeg"), "-y", "-i", input_path,
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "fast",
            output_path,
        ], stdin=subprocess.DEVNULL, capture_output=True, check=True, timeout=120)

        return output_path

    @staticmethod
    def extract_last_frame(video_path: str, output_path: str) -> str:
        """提取视频最后一帧为图片。"""
        logger.info(f"[Compositor] Extracting last frame: {video_path} → {output_path}")
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        import subprocess
        subprocess.run([
            resolve_binary("ffmpeg"), "-y",
            "-sseof", "-1",
            "-i", video_path,
            "-frames:v", "1",
            "-update", "1",
            output_path,
        ], stdin=subprocess.DEVNULL, capture_output=True, check=True, timeout=30)

        return output_path

    @staticmethod
    def generate_silent_audio(duration_sec: float, output_path: str) -> str:
        """生成指定时长的静音音频文件。"""
        logger.info(f"[Compositor] Generating silent audio: {duration_sec:.1f}s → {output_path}")
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        import subprocess
        subprocess.run([
            resolve_binary("ffmpeg"), "-y",
            "-f", "lavfi",
            "-i", "anullsrc=r=44100:cl=mono",
            "-t", str(duration_sec),
            "-c:a", "libmp3lame", "-q:a", "4",
            output_path,
        ], stdin=subprocess.DEVNULL, capture_output=True, check=True, timeout=30)

        return output_path

    @staticmethod
    def freeze_last_frame(video_path: str, freeze_duration: float, output_path: str) -> str:
        """将视频最后一帧冻结指定时长，输出新视频。

        用于视频-音频对齐：当视频时长不足时，冻结尾帧补齐。
        输出时长 = 原视频时长 + freeze_duration。

        Args:
            video_path: 输入视频
            freeze_duration: 冻结时长（秒）
            output_path: 输出视频路径
        """
        logger.info(f"[Compositor] Freezing last frame: {freeze_duration:.1f}s → {output_path}")
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        import subprocess

        # 方案 1（首选）：ffmpeg tpad 滤镜克隆尾帧。
        # 单输入单滤镜，输出 = 原视频 + freeze_duration 的尾帧定格，且保留音频轨。
        # 注意：勿再用 -t {freeze_duration}，那会把整个输出截断成只剩冻结段。
        try:
            subprocess.run([
                resolve_binary("ffmpeg"), "-y",
                "-i", video_path,
                "-vf", f"tpad=stop_mode=clone:stop_duration={freeze_duration}",
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac",
                output_path,
            ], stdin=subprocess.DEVNULL, capture_output=True, check=True, timeout=120)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"[Compositor] freeze via tpad succeeded: {output_path}")
                return output_path
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode(errors="replace")[:500] if e.stderr else "no stderr"
            logger.warning(f"[Compositor] tpad freeze failed, trying moviepy fallback: {stderr}")
        except subprocess.TimeoutExpired:
            logger.warning("[Compositor] tpad freeze timed out, trying moviepy fallback")

        # 方案 2（回退）：moviepy 拼接原视频 + 尾帧定格。
        # 使用 get_frame + ImageClip 构造定格（moviepy 2.x 无 to_ImageClip(duration=...) API）。
        from moviepy import ImageClip, VideoFileClip, concatenate_videoclips

        clip = VideoFileClip(video_path)
        final = None
        try:
            # 取接近末尾的帧（duration-0.01 避免越界）
            last_frame_img = clip.get_frame(max(clip.duration - 0.01, 0))
            last_frame = ImageClip(last_frame_img, duration=freeze_duration)
            final = concatenate_videoclips([clip, last_frame], method="compose")
            final.write_videofile(output_path, logger=None, preset="fast")
        finally:
            clip.close()
            if final is not None:
                final.close()

        return output_path

    @staticmethod
    def list_available_luts(luts_dir: Optional[str] = None) -> Dict[str, str]:
        """列出可用的 3D LUT 文件。"""
        if luts_dir is None:
            here = os.path.dirname(os.path.abspath(__file__))
            luts_dir = os.path.normpath(os.path.join(here, "..", "..", "resource", "luts"))

        if not os.path.isdir(luts_dir):
            return {}

        luts = {}
        for fname in os.listdir(luts_dir):
            if fname.lower().endswith(".cube"):
                key = os.path.splitext(fname)[0]
                luts[key] = os.path.join(luts_dir, fname)
        return luts

    @staticmethod
    def apply_lut(video_path: str, lut_path: str, output_path: str) -> str:
        """使用 3D LUT (.cube) 为视频进行电影级调色与 AI 塑料感消除。

        Args:
            video_path: 输入视频
            lut_path: 3D LUT 文件路径 (.cube)
            output_path: 输出视频路径
        """
        if not os.path.exists(lut_path):
            raise FileNotFoundError(f"LUT file not found: {lut_path}")

        logger.info(f"[Compositor] Applying 3D LUT: {lut_path} → {output_path}")
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        # Windows 路径兼容处理: ffmpeg 滤镜中反斜杠需转义为正斜杠，冒号需转义
        lut_filter_path = lut_path.replace("\\", "/").replace(":", "\\:")

        import subprocess
        subprocess.run([
            resolve_binary("ffmpeg"), "-y",
            "-i", video_path,
            "-vf", f"lut3d='{lut_filter_path}'",
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "copy",
            output_path,
        ], stdin=subprocess.DEVNULL, capture_output=True, check=True, timeout=300)

        return output_path

    @staticmethod
    def detect_scene_changes(
        video_path: str,
        threshold: float = 0.15,
        min_interval_s: float = 2.0,
        max_scenes: int = 50
    ) -> List[float]:
        """使用 FFmpeg 场景切换检测提取时间戳（秒）。

        基于 watch.py 的场景分析算法，通过 select='gt(scene,{threshold})' 识别关键切镜。
        """
        import re
        import subprocess

        logger.info(f"[Compositor] Detecting scene changes (threshold={threshold}): {video_path}")
        scene_cmd = [
            resolve_binary("ffmpeg"), "-i", video_path,
            "-filter:v", f"select='gt(scene,{threshold})',showinfo",
            "-vsync", "vfr", "-f", "null", "-"
        ]
        res = subprocess.run(scene_cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=600)

        # 从 showinfo 日志提取 pts_time
        pts_times = [float(m.group(1)) for m in re.finditer(r"pts_time:([\d.]+)", res.stderr)]

        # 去重并应用最小间隔过滤
        pts_times = sorted(set(pts_times))
        filtered = []
        last_t = -min_interval_s
        for t in pts_times:
            if t - last_t >= min_interval_s:
                filtered.append(round(t, 3))
                last_t = t
            if len(filtered) >= max_scenes:
                break

        return filtered

    @staticmethod
    def extract_scene_keyframes(
        video_path: str,
        output_dir: str,
        threshold: float = 0.15,
        min_interval_s: float = 2.0,
        max_scenes: int = 30,
        width: int = 1280
    ) -> List[dict]:
        """多线程并行提取视频分镜关键帧。"""
        import subprocess
        from concurrent.futures import ThreadPoolExecutor

        os.makedirs(output_dir, exist_ok=True)
        timestamps = VideoProcessor.detect_scene_changes(video_path, threshold, min_interval_s, max_scenes)

        if not timestamps:
            timestamps = [0.0]

        def _grab(item):
            idx, ts = item
            fname = f"scene_{idx+1:03d}_{int(ts)}s.jpg"
            fpath = os.path.join(output_dir, fname)
            cmd = [
                resolve_binary("ffmpeg"), "-y",
                "-ss", str(ts),
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "3",
                "-vf", f"scale='min({width},iw)':-1",
                fpath
            ]
            r = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, timeout=120)
            if r.returncode == 0 and os.path.exists(fpath):
                return {
                    "scene_number": idx + 1,
                    "timestamp_s": ts,
                    "frame_path": fpath,
                    "filename": fname
                }
            return None

        tasks = list(enumerate(timestamps))
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(_grab, tasks))

        keyframes = [res for res in results if res is not None]
        logger.info(f"[Compositor] Extracted {len(keyframes)} scene keyframes to {output_dir}")
        return keyframes

