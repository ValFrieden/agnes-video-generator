"""杂项路由：首页、回归测试清理。"""
from __future__ import annotations

import json
import logging
import os
import shutil

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.async_io import read_text
from core.config import get_working_dir
from core.i18n_backend import translate

logger = logging.getLogger(__name__)

router = APIRouter(tags=["utility"])


@router.get("/")
async def root():
    index_path = os.path.join(os.path.dirname(__file__), "..", "..", "static", "index.html")
    index_path = os.path.abspath(index_path)
    if os.path.exists(index_path):
        # 入口页必须禁缓存：index.html 引用带内容 hash 的 /static/assets/*，
        # 重新构建后旧 hash 文件即被删除——浏览器若缓存旧入口页，会去加载
        # 已不存在的 JS，导致整个前端（含任务列表）静默失效。
        # no-cache = 每次向服务器校验（配合 ETag/Last-Modified 仍可 304），assets 本身不受影响。
        return FileResponse(index_path, headers={"Cache-Control": "no-cache"})
    return {"message": "Agnes Video Generator API"}


@router.post("/api/cleanup-regression")
async def cleanup_regression():
    """安全清理回归测试产物（报告、日志、任务目录）。

    只删除产物清单中记录的内容，不影响用户原有任务数据。
    """
    working_dir = get_working_dir()
    manifest_path = os.path.join(working_dir, ".regression_manifest.json")

    if not os.path.exists(manifest_path):
        raise HTTPException(
            status_code=404,
            detail=translate("utility.regression_manifest_missing"))

    try:
        manifest = json.loads(await read_text(manifest_path))
    except (json.JSONDecodeError, OSError) as e:
        raise HTTPException(
            status_code=500,
            detail=translate("utility.manifest_read_failed", reason=str(e)))

    removed_dirs = 0
    removed_files = 0
    errors: list = []
    project_root = os.path.dirname(os.path.abspath(__file__)) + os.sep + ".." + os.sep + ".."
    project_root = os.path.abspath(project_root)
    upload_dir = os.path.join(working_dir, "uploads")

    # 1. 清理任务目录
    for dir_name in manifest.get("task_dirs", []):
        dir_path = os.path.join(working_dir, dir_name)
        if os.path.isdir(dir_path):
            try:
                shutil.rmtree(dir_path)
                removed_dirs += 1
            except OSError as e:
                logger.warning(f"[Cleanup] 删除目录失败 {dir_name}: {e}")
                errors.append(translate("utility.cleanup_dir_failed", name=dir_name))

    # 2. 清理上传文件
    for fname in manifest.get("uploads", []):
        fpath = os.path.join(upload_dir, fname)
        if os.path.isfile(fpath):
            try:
                os.remove(fpath)
                removed_files += 1
            except OSError as e:
                logger.warning(f"[Cleanup] 删除上传文件失败 {fname}: {e}")
                errors.append(translate("utility.cleanup_upload_failed", name=fname))

    # 3. 清理报告文件
    for rel_path in manifest.get("reports", []):
        abs_path = os.path.join(project_root, rel_path)
        if os.path.isfile(abs_path):
            try:
                os.remove(abs_path)
                removed_files += 1
            except OSError as e:
                logger.warning(f"[Cleanup] 删除报告失败 {rel_path}: {e}")
                errors.append(translate("utility.cleanup_report_failed", name=rel_path))

    # 4. 清理服务器日志
    log_rel = manifest.get("server_log", "")
    if log_rel:
        log_path = os.path.join(project_root, log_rel)
        if os.path.isfile(log_path):
            try:
                os.remove(log_path)
                removed_files += 1
            except OSError as e:
                logger.warning(f"[Cleanup] 删除日志失败: {e}")
                errors.append(translate("utility.cleanup_log_failed"))

    # 5. 清理清单本身
    try:
        os.remove(manifest_path)
        removed_files += 1
    except OSError as e:
        logger.warning(f"[Cleanup] 删除清单失败: {e}")
        errors.append(translate("utility.cleanup_manifest_failed"))

    scenarios_cleaned = len(manifest.get("scenarios", {}))
    logger.info(
        f"[Cleanup] 回归清理完成: {removed_dirs} 目录, "
        f"{removed_files} 文件, {scenarios_cleaned} 场景")

    return {
        "ok": len(errors) == 0,
        "removed_dirs": removed_dirs,
        "removed_files": removed_files,
        "scenarios_cleaned": scenarios_cleaned,
        "errors": errors,
    }


class ExtractScenesRequest(BaseModel):
    video_path: str
    threshold: float = 0.15
    min_interval_s: float = 2.0
    max_scenes: int = 30
    width: int = 1280


@router.get("/api/tools/luts")
async def get_available_luts():
    """获取系统内置的电影级 3D LUT 调色预设列表。"""
    from core.compositor.processor import VideoProcessor
    luts = VideoProcessor.list_available_luts()
    descriptions = {
        "cinematic_teal_orange": "好莱坞经典青橙调色 (Teal & Orange)：阴影冷青，肤色与高光温暖，增强画面戏剧张力与景深感",
        "clean_film_anti_plastic": "胶片质感抗塑料感滤镜 (Anti-Plastic)：消除 AI 生成视频常见的高光塑料反光与数码过饱和",
        "warm_vintage": "复古暖调胶片 (Warm Vintage)：柔和高光压缩与温暖微黄底色，适合怀旧与情感向叙事"
    }
    items = []
    for k, v in luts.items():
        items.append({
            "id": k,
            "name": k.replace("_", " ").title(),
            "description": descriptions.get(k, "Professional 3D LUT Color Grade"),
            "path": v
        })
    return {"ok": True, "luts": items}


@router.post("/api/tools/extract-scenes")
async def extract_scenes(req: ExtractScenesRequest):
    """使用 FFmpeg 场景切变检测算法，自动提取视频关键帧与分镜 Storyboard。"""
    from core.compositor.processor import VideoProcessor
    from core.path_security import safe_workspace_path

    try:
        validated_video = safe_workspace_path(req.video_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid video path: {e}")

    if not os.path.isfile(validated_video):
        raise HTTPException(status_code=404, detail="Video file not found")

    working_dir = get_working_dir()
    video_basename = os.path.splitext(os.path.basename(validated_video))[0]
    out_dir = os.path.join(working_dir, "storyboards", video_basename)

    import asyncio
    keyframes = await asyncio.to_thread(
        VideoProcessor.extract_scene_keyframes,
        validated_video,
        out_dir,
        req.threshold,
        req.min_interval_s,
        req.max_scenes,
        req.width
    )

    return {
        "ok": True,
        "video": req.video_path,
        "scene_count": len(keyframes),
        "output_dir": out_dir,
        "scenes": keyframes
    }

