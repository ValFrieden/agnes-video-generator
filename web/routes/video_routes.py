"""视频下载 + 中间产物管理路由。"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import mimetypes
import os
import shutil
import tempfile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from core.api.chat_providers import get_or_build_text_chat_client
from core.api.image_providers import create_image_provider
from core.artifacts import (
    apply_cascade_plan,
    build_checkpoint_manifest,
    get_cascade_plan,
    list_artifacts,
    resolve_artifact,
    write_checkpoint_manifest,
)
from core.async_io import read_text, write_bytes
from core.config import api_key_missing_msg, get_api_key, get_working_dir
from core.dependency_graph import get_dependency_graph
from core.i18n_backend import get_current_lang, translate
from core.path_security import UnsafePathError, safe_join
from core.task_manager import TaskManager
from models.task import StepStatus
from utils.network import describe_network_error
from web import app_state, helpers
from web.log_safe import safe_log

logger = logging.getLogger(__name__)

router = APIRouter(tags=["video", "artifacts"])

# Logikcheck Befund 6：产物回填上传的体积上限（与任务创建上传一致）
_MAX_UPLOAD_BYTES = 50 * 1024 * 1024

# 产物类别 → MIME 类型映射
_ARTIFACT_MEDIA_TYPES = {
    "image": "image/png",
    "video": "video/mp4",
    "audio": "audio/mpeg",
    "text": "text/plain; charset=utf-8",
    "json": "application/json; charset=utf-8",
    "subtitle": "text/plain; charset=utf-8",
}


@router.get("/api/video/{task_id}")
async def serve_video(task_id: str, download: bool = False, variant: str = ""):
    dir_name = helpers.find_dir_name(task_id)
    try:
        task_dir = safe_join(get_working_dir(), dir_name)
    except UnsafePathError:
        raise HTTPException(status_code=404, detail="Video not found")
    filename = "processed_video.mp4" if variant == "processed" else "final_video.mp4"
    video_path = os.path.join(task_dir, filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")
    # Logikcheck Befund 4：download=1 时以附件形式下发（Content-Disposition: attachment），
    # 前端结果区的「下载视频」链接直接复用本端点。
    if download:
        dl_name = f"{task_id}_edited.mp4" if variant == "processed" else f"{task_id}.mp4"
        return FileResponse(video_path, media_type="video/mp4", filename=dl_name)
    return FileResponse(video_path, media_type="video/mp4")


@router.post("/api/tasks/{task_id}/postprocess")
async def postprocess_task_video(
    task_id: str,
    start_sec: float = Form(0.0),
    end_sec: float = Form(0.0),
    lut_id: str = Form(""),
    aspect: str = Form("keep"),
):
    """对已完成的成片执行轻量后处理（裁剪起止秒、3D LUT 调色、画幅裁切导出）。"""
    import subprocess
    from core.compositor.ffmpeg_tool import resolve_binary
    from core.compositor.processor import VideoProcessor

    dir_name = helpers.find_dir_name(task_id)
    try:
        task_dir = safe_join(get_working_dir(), dir_name)
    except UnsafePathError:
        raise HTTPException(status_code=404, detail="Video not found")

    src_video = os.path.join(task_dir, "final_video.mp4")
    if not os.path.isfile(src_video):
        raise HTTPException(status_code=404, detail="Final video not found")

    if start_sec < 0 or (end_sec > 0 and end_sec <= start_sec):
        raise HTTPException(status_code=422, detail="Invalid trim range")
    if aspect not in ("keep", "9:16", "16:9", "1:1"):
        raise HTTPException(status_code=422, detail="Unsupported aspect ratio")

    out_video = os.path.join(task_dir, "processed_video.mp4")

    def _run_ffmpeg() -> None:
        filters: list[str] = []
        if aspect == "9:16":
            filters.append("crop='min(iw,ih*9/16)':'min(ih,iw*16/9)'")
        elif aspect == "16:9":
            filters.append("crop='min(iw,ih*16/9)':'min(ih,iw*9/16)'")
        elif aspect == "1:1":
            filters.append("crop='min(iw,ih)':'min(iw,ih)'")

        if lut_id.strip():
            lut_path = VideoProcessor.list_available_luts().get(lut_id.strip())
            if lut_path and os.path.isfile(lut_path):
                lut_filter_path = lut_path.replace("\\", "/").replace(":", "\\:")
                filters.append(f"lut3d='{lut_filter_path}'")

        cmd = [resolve_binary("ffmpeg"), "-y"]
        if start_sec > 0:
            cmd += ["-ss", f"{start_sec:.3f}"]
        if end_sec > start_sec:
            cmd += ["-to", f"{end_sec:.3f}"]
        cmd += ["-i", src_video]
        if filters:
            cmd += ["-vf", ",".join(filters)]
        cmd += ["-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "-movflags", "+faststart", out_video]
        subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, check=True, timeout=300)

    try:
        await asyncio.to_thread(_run_ffmpeg)
    except subprocess.CalledProcessError as e:
        err = (e.stderr or b"").decode(errors="replace")[:300]
        raise HTTPException(status_code=500, detail=f"FFmpeg postprocess failed: {err}")

    return {
        "ok": True,
        "video_url": f"/api/video/{task_id}?variant=processed&t={int(os.path.getmtime(out_video))}",
        "download_url": f"/api/video/{task_id}?variant=processed&download=1",
    }


@router.get("/api/tasks/{task_id}/artifacts")
async def list_task_artifacts(task_id: str):
    """列举任务的所有中间产物（含存在性检测）。"""
    dir_name = helpers.find_dir_name(task_id)
    tm = TaskManager(task_id, dir_name=dir_name)
    state = tm.load()
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")

    artifacts = list_artifacts(state, tm.task_dir)
    return {
        "ok": True,
        "task_type": state.task_type.value,
        "task_status": state.status.value if state.status else "pending",
        "dir_name": dir_name,
        "artifacts": [
            {
                "artifact_id": a.artifact_id,
                "step_key": a.step_key,
                "label_key": a.label_key,
                "category": a.category,
                "scope": a.scope,
                "scope_index": a.scope_index,
                "exists": a.exists,
                "size": a.size,
                "deletable": a.deletable,
                # v5.x 产物规范前置：暴露相对路径 / 字段说明 / 预览 URL
                "file_relpath": a.file_relpath,
                "schema_hint": a.schema_hint,
                "preview_url": (
                    f"/api/tasks/{task_id}/artifacts/{a.artifact_id}/file"
                    if a.file_relpath else ""
                ),
            }
            for a in artifacts
        ],
    }


@router.get("/api/tasks/{task_id}/artifacts/{artifact_id}/file")
async def serve_artifact_file(task_id: str, artifact_id: str):
    """安全地服务中间产物文件。"""
    dir_name = helpers.find_dir_name(task_id)
    tm = TaskManager(task_id, dir_name=dir_name)
    state = tm.load()
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")

    artifact = resolve_artifact(artifact_id, state, tm.task_dir)
    if not artifact or not artifact.file_relpath:
        raise HTTPException(status_code=404, detail="Artifact not found")
    if not artifact.exists:
        raise HTTPException(status_code=404, detail="Artifact file not found")

    abs_path = os.path.join(tm.task_dir, artifact.file_relpath)
    # 路径穿越防护
    real_task_dir = os.path.realpath(tm.task_dir)
    real_abs_path = os.path.realpath(abs_path)
    if not real_abs_path.startswith(real_task_dir + os.sep):
        raise HTTPException(status_code=403, detail="Access denied")

    media_type = _ARTIFACT_MEDIA_TYPES.get(artifact.category, "application/octet-stream")
    return FileResponse(real_abs_path, media_type=media_type)


@router.get("/api/tasks/{task_id}/manifest")
async def get_task_manifest(task_id: str):
    """返回任务产物清单（manifest.json）。

    清单由流水线运行开始/结束时自动落盘；若不存在（如排队中或旧任务）
    则现场构建并写盘。包含结构化产物（path/schema_hint/preview_url）
    与通用文件树两部分，是 v6.0 手动模式 checkpoint 的数据基础。
    """
    dir_name = helpers.find_dir_name(task_id)
    tm = TaskManager(task_id, dir_name=dir_name)
    state = tm.load()
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")

    from core.artifacts import build_manifest, write_manifest

    manifest_path = os.path.join(tm.task_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        write_manifest(state, tm.task_dir)
    try:
        manifest = json.loads(await read_text(manifest_path))
    except (OSError, ValueError):
        # 清单损坏/不可读 → 现场重建
        manifest = build_manifest(state, tm.task_dir)
    return {"ok": True, **manifest}


@router.get("/api/tasks/{task_id}/manifest.md")
async def get_task_manifest_md(task_id: str):
    """返回任务目录说明文件 MANIFEST.md（供用户与外部 Agent 阅读）。"""
    dir_name = helpers.find_dir_name(task_id)
    tm = TaskManager(task_id, dir_name=dir_name)
    state = tm.load()
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")

    from core.artifacts import write_manifest_md

    md_path = os.path.join(tm.task_dir, "MANIFEST.md")
    if not os.path.exists(md_path):
        write_manifest_md(state, tm.task_dir)
    if not os.path.exists(md_path):
        raise HTTPException(status_code=404, detail="Manifest not available")
    return FileResponse(md_path, media_type="text/markdown; charset=utf-8")


@router.get("/api/tasks/{task_id}/artifacts/{artifact_id}/cascade-preview")
async def preview_artifact_cascade(task_id: str, artifact_id: str):
    """预览删除产物的级联计划（不执行删除）。"""
    dir_name = helpers.find_dir_name(task_id)
    tm = TaskManager(task_id, dir_name=dir_name)
    state = tm.load()
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")

    artifact = resolve_artifact(artifact_id, state, tm.task_dir)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    plan = get_cascade_plan(artifact_id, state, tm.task_dir)
    if not plan:
        raise HTTPException(status_code=400, detail="Cannot compute cascade plan")

    # 只返回存在的文件
    existing_files = []
    for f in plan.files_to_delete:
        abs_path = os.path.join(tm.task_dir, f)
        if os.path.exists(abs_path):
            existing_files.append(f)

    return {
        "ok": True,
        "artifact_id": artifact_id,
        "files_to_delete": existing_files,
        "steps_to_reset": plan.steps_to_reset,
    }


@router.delete("/api/tasks/{task_id}/artifacts/{artifact_id}")
async def delete_task_artifact(task_id: str, artifact_id: str):
    """删除指定中间产物（含级联删除后续产物 + 状态回退）。"""
    # Logikcheck Befund 7：状态读改写全程持有任务锁，与 resume/stop/create 串行化，
    # 避免与运行中的 pipeline 或并发的审批操作互相覆盖状态文件。
    async with app_state.get_pipeline_lock(task_id):
        # 运行中任务保护（已停止的 pipeline 允许删除产物）
        if task_id in app_state.active_pipelines:
            pipeline = app_state.active_pipelines[task_id]
            if not pipeline._stop_event.is_set():
                raise HTTPException(status_code=409, detail="Task is running, please stop it first")

        dir_name = helpers.find_dir_name(task_id)
        tm = TaskManager(task_id, dir_name=dir_name)
        state = tm.load()
        if not state:
            raise HTTPException(status_code=404, detail="Task not found")

        artifact = resolve_artifact(artifact_id, state, tm.task_dir)
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact not found")

        plan = get_cascade_plan(artifact_id, state, tm.task_dir)
        if not plan:
            raise HTTPException(status_code=400, detail="Cannot compute cascade plan")

        # 1. 删除文件
        deleted_files = []
        real_task_dir = os.path.realpath(tm.task_dir)
        for f in plan.files_to_delete:
            abs_path = os.path.join(tm.task_dir, f)
            real_abs_path = os.path.realpath(abs_path)
            # 路径穿越防护
            if not real_abs_path.startswith(real_task_dir + os.sep):
                continue
            if os.path.exists(abs_path) and os.path.isfile(abs_path):
                try:
                    os.remove(abs_path)
                    deleted_files.append(f)
                except OSError as e:
                    logger.warning(f"[Artifacts] Failed to delete {f}: {e}")

        # 2. 应用级联计划到 state
        update_kwargs = apply_cascade_plan(state, plan)

        # 3. 持久化
        tm.update_state(**update_kwargs)

    logger.info(
        "[Artifacts] Deleted %d files for task %s, artifact=%s, reset_steps=%s",
        len(deleted_files), safe_log(task_id), safe_log(artifact_id),
        plan.steps_to_reset,
    )

    return {
        "ok": True,
        "deleted_files": deleted_files,
        "reset_steps": plan.steps_to_reset,
        "task_status": state.status.value if state.status else "pending",
    }


@router.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务及其磁盘上全部生成文件（优化 3）。

    运行中/排队中任务拒绝删除。删除范围：任务工作目录（含状态文件、全部产物、
    上传文件）。删除后任务从任务列表消失，不可恢复。
    """
    # 1. 运行中保护（含排队中）
    if task_id in app_state.active_pipelines:
        pipeline = app_state.active_pipelines.get(task_id)
        if pipeline is not None and not getattr(pipeline, "_stop_event", None).is_set():
            raise HTTPException(
                status_code=400,
                detail="Cannot delete a running task. Stop it first.",
            )
    if task_id in app_state._queued_tasks:
        raise HTTPException(
            status_code=400,
            detail="Task is queued. Stop it before deleting.",
        )

    # 2. 定位任务工作目录
    dir_name = helpers.find_dir_name(task_id)
    removed_dir = False
    if dir_name:
        # 路径穿越防护：先经 realpath 解析，确认目录位于工作目录内才允许删除
        real_root = os.path.realpath(get_working_dir())
        real_task_dir = os.path.realpath(os.path.join(get_working_dir(), dir_name))
        if real_task_dir != real_root and real_task_dir.startswith(real_root + os.sep):
            # Logikcheck Befund 8: find_dir_name fällt bei unbekannter ID auf die ID
            # selbst zurück. Ohne diese Prüfung löschte DELETE /api/tasks/uploads den
            # gemeinsamen uploads/-Ordner. Gelöscht wird nur, was eine Aufgabe ist:
            # eine task_state.json trägt (auch eine unlesbare) oder in der Liste steht.
            if not (
                os.path.isfile(os.path.join(real_task_dir, "task_state.json"))
                or _task_exists(task_id)
            ):
                raise HTTPException(status_code=404, detail="Task not found")
            if os.path.exists(real_task_dir):
                shutil.rmtree(real_task_dir, ignore_errors=True)
                # Logikcheck Befund 8: Unter Windows vor dem Setzen von removed_dir verifizieren,
                # dass das Verzeichnis tatsächlich entfernt wurde (Dateisperren können rmtree lautlos blockieren).
                if os.path.exists(real_task_dir):
                    import time
                    time.sleep(0.05)
                    shutil.rmtree(real_task_dir, ignore_errors=True)
                if not os.path.exists(real_task_dir):
                    removed_dir = True
                    logger.info("[Delete] Task %s directory removed: %s",
                                safe_log(task_id), real_task_dir)
                else:
                    removed_dir = False
                    logger.warning("[Delete] Task %s directory still exists on disk after rmtree (possibly file locked by OS): %s",
                                   safe_log(task_id), real_task_dir)
        else:
            logger.warning("[Delete] Unsafe task dir for %s, skipped: %s",
                           safe_log(task_id), safe_log(dir_name))

    # 3. 从活动注册表 / 排队列表摘除
    app_state.active_pipelines.pop(task_id, None)
    app_state._queued_tasks.pop(task_id, None)
    app_state.release_pipeline_lock(task_id)
    # GA 埋点：同步清理上游报错内存聚合（防缓慢增长）
    try:
        from core.api.error_collector import clear_task_upstream_errors

        clear_task_upstream_errors(task_id)
    except Exception:
        pass

    # Logikcheck Befund 8（Sammelliste）：任务删除后清理共享 uploads/ 中以该任务
    # id 为前缀的上传文件，以及画廊缩略图缓存，避免孤儿文件长期堆积。
    try:
        _upload_dir = helpers.get_upload_dir()
        if os.path.isdir(_upload_dir):
            for name in os.listdir(_upload_dir):
                if name.startswith(f"{task_id}_"):
                    try:
                        os.remove(os.path.join(_upload_dir, name))
                    except OSError as e:
                        logger.warning("[Delete] Failed to remove upload %s: %s", name, e)
    except OSError as e:
        logger.warning("[Delete] Failed to scan uploads dir: %s", e)
    try:
        from core.gallery_cache import invalidate_thumb

        invalidate_thumb(task_id)
    except Exception as e:
        logger.warning("[Delete] Gallery cache invalidation failed: %s", e)

    if not removed_dir and not _task_exists(task_id):
        # 任务目录不存在且任务已不在列表中：视为不存在
        raise HTTPException(status_code=404, detail="Task not found")

    return {"ok": True, "task_id": task_id, "message": "Task deleted", "removed_dir": removed_dir}


def _task_exists(task_id: str) -> bool:
    """检查任务是否仍存在于任务列表（状态文件存在）。"""
    from core.task_manager import TaskManager

    tm = TaskManager("_")
    for t in tm.list_tasks():
        if t["task_id"] == task_id:
            return True
    return False


# ═══════════════════════════════════════════════════════════════
# v6.0 手动模式：检查点 + 影响预计算 + 产物回填 + 确认/重生成
# ═══════════════════════════════════════════════════════════════


@router.get("/api/tasks/{task_id}/checkpoints")
async def list_task_checkpoints(task_id: str):
    """返回任务按检查点分组的产物清单（checkpoint.json 数据）。

    供手动模式检查点等待页使用；若 checkpoint.json 未落盘则现场构建。
    """
    dir_name = helpers.find_dir_name(task_id)
    tm = TaskManager(task_id, dir_name=dir_name)
    state = tm.load()
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")

    ckpt_path = os.path.join(tm.task_dir, "checkpoint.json")
    if not os.path.exists(ckpt_path):
        write_checkpoint_manifest(state, tm.task_dir)
    try:
        data = json.loads(await read_text(ckpt_path))
    except (OSError, ValueError):
        data = build_checkpoint_manifest(state, tm.task_dir)

    # 补充当前检查点（实时读取状态，避免 checkpoint.json 过期）
    mc = getattr(state, "manual_config", None)
    data["current_checkpoint"] = (mc.current_checkpoint if mc else "") or ""
    return {"ok": True, **data}


@router.get("/api/tasks/{task_id}/checkpoints/{checkpoint}")
async def get_task_checkpoint(task_id: str, checkpoint: str):
    """返回单个检查点的产物列表与状态。"""
    dir_name = helpers.find_dir_name(task_id)
    tm = TaskManager(task_id, dir_name=dir_name)
    state = tm.load()
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")

    data = build_checkpoint_manifest(state, tm.task_dir)
    groups = data.get("checkpoints", {})
    if checkpoint not in groups:
        raise HTTPException(status_code=404, detail=f"Checkpoint '{checkpoint}' not found")

    # 补产物绝对路径 + 任务目录（供通道 2/3 展示产物路径）
    group = groups[checkpoint]
    for a in group.get("artifacts", []):
        rel = a.get("path") or ""
        a["abs_path"] = os.path.join(tm.task_dir, rel) if rel else ""
    return {
        "ok": True,
        "checkpoint": checkpoint,
        "working_dir": tm.task_dir,
        **group,
    }


@router.get("/api/tasks/{task_id}/checkpoints/{checkpoint}/impact")
async def preview_checkpoint_impact(
    task_id: str,
    checkpoint: str,
    modified_artifact_ids: str = "",
    param_updates: str = "",
):
    """影响预计算（PRD §4.5 / §5.2）：只计算不落盘。

    query 参数（JSON 字符串）：
        modified_artifact_ids: ["creative:script:scene_prompt"] 或 ["creative:video:2"]
        param_updates: {"resolution": "768x1152"}

    返回 ImpactPlan{affected, retained, steps_to_reset, affected_checkpoints}，
    供前端「修改前提示」弹窗展示将删除重跑的产物。
    """
    dir_name = helpers.find_dir_name(task_id)
    tm = TaskManager(task_id, dir_name=dir_name)
    state = tm.load()
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        modified = json.loads(modified_artifact_ids) if modified_artifact_ids else []
        params = json.loads(param_updates) if param_updates else None
    except ValueError:
        raise HTTPException(status_code=422, detail=translate("checkpoint.json_required"))

    if not isinstance(modified, list):
        raise HTTPException(status_code=422, detail=translate("checkpoint.artifact_ids_not_array"))

    graph = get_dependency_graph(state.task_type)
    # Logikcheck Befund 10: Vorschau des „Bestätigen und fortsetzen“. Geänderte Ergebnisse
    # bleiben erhalten und dürfen im Dialog nicht als „wird gelöscht“ erscheinen.
    plan = graph.compute_impact(state, modified, params, keep_modified=True)
    return {"ok": True, "checkpoint": checkpoint, **plan.to_dict()}


@router.post("/api/tasks/{task_id}/artifacts/{artifact_id}/upload")
async def upload_task_artifact(
    task_id: str,
    artifact_id: str,
    file: UploadFile = File(...),
):
    """覆盖回填产物（PRD §4.4 / 通道2）。

    仅允许在任务暂停（PENDING + current_checkpoint）或未运行时回填；
    写入前校验路径穿越 + 覆盖后落盘 manifest / checkpoint。
    """
    # Logikcheck Befund 7：与 delete_task_artifact 相同，状态读改写持有任务锁。
    async with app_state.get_pipeline_lock(task_id):
        # 运行中保护
        if task_id in app_state.active_pipelines:
            pipeline = app_state.active_pipelines[task_id]
            if not pipeline._stop_event.is_set():
                raise HTTPException(status_code=409, detail="Task is running, please stop/pause it first")

        dir_name = helpers.find_dir_name(task_id)
        tm = TaskManager(task_id, dir_name=dir_name)
        state = tm.load()
        if not state:
            raise HTTPException(status_code=404, detail="Task not found")

        artifact = resolve_artifact(artifact_id, state, tm.task_dir)
        if not artifact or not artifact.file_relpath:
            raise HTTPException(status_code=404, detail="Artifact not found")
        if not artifact.deletable:
            raise HTTPException(status_code=400, detail="Artifact is not editable")

        # 路径穿越防护
        real_task_dir = os.path.realpath(tm.task_dir)
        abs_path = os.path.join(tm.task_dir, artifact.file_relpath)
        real_abs_path = os.path.realpath(abs_path)
        if not real_abs_path.startswith(real_task_dir + os.sep):
            raise HTTPException(status_code=403, detail="Access denied")

        # Logikcheck Befund 6：回填上传同样按上限封顶读取
        content = await file.read(_MAX_UPLOAD_BYTES + 1)
        if len(content) > _MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=translate(
                    "validation.upload_too_large", get_current_lang(),
                    max_mb=_MAX_UPLOAD_BYTES // (1024 * 1024),
                ),
            )
        os.makedirs(os.path.dirname(real_abs_path), exist_ok=True)
        await write_bytes(real_abs_path, content)

        # 标记脏：记录回填产物 id（手动模式）
        mc = getattr(state, "manual_config", None)
        if mc is not None:
            if artifact_id not in mc.modified_artifacts:
                mc.modified_artifacts.append(artifact_id)
            tm.update_state(manual_config=mc)

        # 刷新清单
        write_checkpoint_manifest(state, tm.task_dir)

    logger.info("[Artifacts] Uploaded %s for task %s (%d bytes)",
                safe_log(artifact_id), safe_log(task_id), len(content))
    return {"ok": True, "artifact_id": artifact_id, "size": len(content)}


@router.post("/api/tasks/{task_id}/checkpoints/{checkpoint}/approve")
async def approve_checkpoint(task_id: str, checkpoint: str,
                             modified_artifact_ids: str = Form(""),
                             param_updates: str = Form(""),
                             confirmed: bool = Form(False)):
    """确认产物并继续（PRD §5.2）。

    - 不传 ``confirmed``（或 false）：仅计算影响计划返回，不落盘（等价 impact 预计算）。
    - ``confirmed=true``：落盘删除受影响产物 + 重置步骤 + 标记检查点已确认，
      然后走现有 resume 恢复执行。

    Logikcheck Befund 10：``modified_artifact_ids`` 是用户提供的内容（上传/回填）。
    它们**保留**文件与步骤，只有下游重跑；否则步骤被重置、文件被删，流水线会重新
    生成并覆盖用户的输入。
    """
    return await _approve_checkpoint(
        task_id, checkpoint, modified_artifact_ids, param_updates, confirmed,
        keep_modified=True,
    )


async def _approve_checkpoint(task_id: str, checkpoint: str,
                              modified_artifact_ids: str, param_updates: str,
                              confirmed: bool, *, keep_modified: bool):
    """``approve_checkpoint`` 的实现。``regen`` 以 ``keep_modified=False`` 复用：
    它把检查点自身的产物当作「已修改」传入，目的正是删除并重新生成它们。"""
    dir_name = helpers.find_dir_name(task_id)
    tm = TaskManager(task_id, dir_name=dir_name)
    state = tm.load()
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        modified = json.loads(modified_artifact_ids) if modified_artifact_ids else []
        params = json.loads(param_updates) if param_updates else None
    except ValueError:
        raise HTTPException(status_code=422, detail=translate("checkpoint.json_required"))

    graph = get_dependency_graph(state.task_type)
    plan = graph.compute_impact(state, modified, params, keep_modified=keep_modified)

    if not confirmed:
        # 仅预计算返回，不落盘（前端可据此展示"修改前提示"弹窗）
        return {"ok": True, "checkpoint": checkpoint, "confirmed": False, **plan.to_dict()}

    # ── 确认落盘 ──
    # 1. 删除受影响产物文件 + 应用级联计划到 state
    deleted_files: list[str] = []
    real_task_dir = os.path.realpath(tm.task_dir)
    for aid in plan.affected:
        artifact = resolve_artifact(aid, state, tm.task_dir)
        if artifact and artifact.file_relpath:
            abs_path = os.path.join(tm.task_dir, artifact.file_relpath)
            real_abs_path = os.path.realpath(abs_path)
            if real_abs_path.startswith(real_task_dir + os.sep) and os.path.exists(abs_path) and os.path.isfile(abs_path):
                try:
                    os.remove(abs_path)
                    deleted_files.append(artifact.file_relpath)
                except OSError as e:
                    logger.warning("[Artifacts] Failed to delete %s: %s", artifact.file_relpath, e)

    # 2. 重置受影响步骤状态 + 任务置 PENDING
    update_kwargs: dict = {}
    for step_field in plan.steps_to_reset:
        if hasattr(state, step_field):
            setattr(state, step_field, StepStatus.PENDING)
            update_kwargs[step_field] = StepStatus.PENDING

    # 3. 标记检查点（approve 标记确认；regen 则必须保持未确认以允许重新暂停审查）
    mc = getattr(state, "manual_config", None)
    if mc is not None:
        if keep_modified:
            if checkpoint not in mc.approved_checkpoints:
                mc.approved_checkpoints.append(checkpoint)
            if modified:
                for m in modified:
                    if m not in mc.modified_artifacts:
                        mc.modified_artifacts.append(m)
        else:
            # Regen: 重新生成当前检查点，绝不能提前标记为 approved，也不能作为用户修改加入 modified_artifacts
            if checkpoint in mc.approved_checkpoints:
                mc.approved_checkpoints.remove(checkpoint)
            if modified:
                mc.modified_artifacts = [m for m in mc.modified_artifacts if m not in modified]
        mc.current_checkpoint = ""
        update_kwargs["manual_config"] = mc
    update_kwargs["status"] = StepStatus.PENDING
    state.status = StepStatus.PENDING

    # 4. 持久化
    tm.update_state(**update_kwargs)

    # 5. 刷新清单
    write_checkpoint_manifest(state, tm.task_dir)

    logger.info(
        "[Approve] Task %s checkpoint '%s' approved, deleted=%d, reset=%s",
        safe_log(task_id), safe_log(checkpoint),
        len(deleted_files), plan.steps_to_reset,
    )

    # 6. 走现有 resume 恢复执行
    from web.routes.task_routes import resume_task

    return await resume_task(task_id)


@router.post("/api/tasks/{task_id}/checkpoints/{checkpoint}/regen")
async def regen_checkpoint(task_id: str, checkpoint: str):
    """重新生成当前检查点（PRD §5.2）。

    等价于 approve(modified_artifact_ids=[该检查点全部产物], confirmed=true)：
    重置本检查点全部产物 + 下游，然后 resume 重新生成。
    """
    dir_name = helpers.find_dir_name(task_id)
    tm = TaskManager(task_id, dir_name=dir_name)
    state = tm.load()
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")

    data = build_checkpoint_manifest(state, tm.task_dir)
    groups = data.get("checkpoints", {})
    if checkpoint not in groups:
        raise HTTPException(status_code=404, detail=f"Checkpoint '{checkpoint}' not found")

    # 该检查点全部产物 id
    modified = [a["artifact_id"] for a in groups[checkpoint]["artifacts"]]
    # Befund 10: keep_modified=False — „neu generieren“ soll die Ergebnisse des Prüfpunkts
    # gerade löschen und zurücksetzen, nicht behalten.
    return await _approve_checkpoint(
        task_id, checkpoint, json.dumps(modified), "", True, keep_modified=False,
    )


_TEXT_CATEGORIES = {"json", "subtitle", "text"}
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}


def _text_diff_summary(old: str, new: str, lang: str = "zh") -> str:
    """轻量文本改动摘要（行级差量 + 字符数变化），不依赖外部 diff 库。

    Args:
        old: 原文本。
        new: 新文本。
        lang: UI 语言（v7.0，issue #64），决定摘要文案语种。
    """
    old_lines = [line for line in old.splitlines() if line.strip()]
    new_lines = [line for line in new.splitlines() if line.strip()]
    if old_lines == new_lines:
        if old != new:
            return translate(
                "ai_modify.diff_char_only", lang,
                old_len=len(old), new_len=len(new),
            )
        return translate("ai_modify.diff_no_change", lang)
    added = sum(1 for line in new_lines if line not in set(old_lines))
    removed = sum(1 for line in old_lines if line not in set(new_lines))
    return translate(
        "ai_modify.diff_summary", lang,
        added=added, removed=removed, old_len=len(old), new_len=len(new),
    )


def _read_file_b64(path: str) -> str:
    """同步读取文件并返回 base64 文本（供 to_thread 在线程池执行）。"""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


async def _image_output_to_data_url(output) -> str:
    """将 ImageOutput 转为 base64 data URL（url / b64 两种 fmt 兼备）。"""
    ext = (getattr(output, "ext", None) or "png").lower()
    mime = mimetypes.guess_type(f"x.{ext}")[0] or "image/png"
    if getattr(output, "fmt", None) == "b64":
        raw = output.data
        if "," in raw:
            raw = raw.split(",", 1)[1]
        return f"data:{mime};base64,{raw}"
    # fmt == "url"：下载到临时文件再读回 base64
    fd, tmp = tempfile.mkstemp(suffix=f".{ext}")
    os.close(fd)
    try:
        await output.save(tmp)
        b64 = await asyncio.to_thread(_read_file_b64, tmp)
        return f"data:{mime};base64,{b64}"
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


@router.post("/api/tasks/{task_id}/checkpoints/{checkpoint}/ai-modify")
async def ai_modify_artifact(
    task_id: str,
    checkpoint: str,
    artifact_id: str = Form(...),
    user_request: str = Form(...),
):
    """通道 1：页内 AI 修改（文本 / 图片产物，PRD §5.2 / §4.7）。

    读取目标产物 → 按类型调模型改写 → 返回新内容（**不落盘、不改 state**）；
    前端预览 / 微调后经 ``upload`` 落盘，再走 ``approve`` 重置下游并恢复执行。
    视频 / 音频产物暂不支持，返回 400。
    """
    if not user_request.strip():
        raise HTTPException(status_code=422, detail=translate("ai_modify.user_request_empty"))

    # 运行中保护
    if task_id in app_state.active_pipelines:
        pipeline = app_state.active_pipelines[task_id]
        if not pipeline._stop_event.is_set():
            raise HTTPException(status_code=409, detail="Task is running, please stop/pause it first")

    dir_name = helpers.find_dir_name(task_id)
    tm = TaskManager(task_id, dir_name=dir_name)
    state = tm.load()
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")

    artifact = resolve_artifact(artifact_id, state, tm.task_dir)
    if not artifact or not artifact.file_relpath:
        raise HTTPException(status_code=404, detail="Artifact not found")
    if not artifact.deletable:
        raise HTTPException(status_code=400, detail="Artifact is not editable")

    # 路径穿越防护
    real_task_dir = os.path.realpath(tm.task_dir)
    abs_path = os.path.join(tm.task_dir, artifact.file_relpath)
    real_abs_path = os.path.realpath(abs_path)
    if not real_abs_path.startswith(real_task_dir + os.sep):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.exists(real_abs_path) or not os.path.isfile(real_abs_path):
        raise HTTPException(status_code=404, detail="Artifact file not found")

    api_key = get_api_key()
    if not api_key:
        # v7.0（issue #64）：按任务落盘 ui_language 本地化，避免英文界面看到中文报错
        raise HTTPException(status_code=400, detail=api_key_missing_msg(state.ui_language))

    ui_lang = getattr(state, "ui_language", "") or "zh"
    category = artifact.category
    try:
        if category in _TEXT_CATEGORIES:
            raw = await read_text(real_abs_path)
            chat_api = get_or_build_text_chat_client(api_key=api_key)
            if category == "json":
                parsed = await asyncio.to_thread(
                    chat_api.chat_json,
                    "你是资深视频分镜/编剧编辑器。必须严格保持 JSON 结构与既有字段，"
                    "只按用户要求修改目标字段，禁止新增/删除顶层字段，禁止破坏 JSON 合法性。",
                    f"以下是现有 JSON：\n{raw}\n\n用户要求：{user_request}\n请直接输出修改后的完整 JSON。",
                )
                new_content = json.dumps(parsed, ensure_ascii=False, indent=2)
            else:
                new_content = await asyncio.to_thread(
                    chat_api.chat,
                    "你是资深视频文案/字幕编辑器。保持原格式（SRT 序号与时间轴格式不变、"
                    "文本分段不变），只按用户要求修改内容，输出完整改写结果。",
                    f"以下是现有内容：\n{raw}\n\n用户要求：{user_request}\n请直接输出修改后的完整内容。",
                )
            diff_summary = _text_diff_summary(raw, new_content, lang=ui_lang)
        elif os.path.splitext(artifact.file_relpath)[1].lower() in _IMAGE_EXTS:
            chat_api = get_or_build_text_chat_client(api_key=api_key)
            edit_prompt = await asyncio.to_thread(
                chat_api.chat_multimodal,
                "你是资深图像编辑。基于用户意见，输出一条简洁的中文改写要求，"
                "用于图像编辑模型基于该图重生成。只输出修改要求本身，不超过 150 字。",
                f"用户希望修改这幅图：{user_request}\n请输出修改要求本身。",
                [real_abs_path],
            )
            # v7.3 多 Provider：AI 修改按 UI 所选图片模型路由；参考图（i2i）仅在
            # Provider 支持时生效（t2i-only 模型会带警告忽略，见 image_providers）
            from core.config import get_selected_models

            image_api = create_image_provider(
                api_key=api_key, model=get_selected_models()["image"],
            )
            output = await image_api.generate_single_image(
                prompt=edit_prompt.strip(),
                reference_image_paths=[real_abs_path],
            )
            new_content = await _image_output_to_data_url(output)
            diff_summary = translate(
                "ai_modify.image_regenerated", ui_lang,
                prompt=edit_prompt.strip()[:120],
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=translate(
                    "ai_modify.unsupported_category", ui_lang, category=category,
                ),
            )
    except HTTPException:
        raise
    except Exception as e:
        # v7.0（issue #64）：网络诊断按 ui_language 输出中/英文
        message = describe_network_error(e, lang=ui_lang) or translate(
            "ai_modify.failed", ui_lang, reason=str(e),
        )
        raise HTTPException(status_code=502, detail=message)

    logger.info("[AiModify] %s task %s checkpoint '%s' (category=%s)",
                safe_log(artifact_id), safe_log(task_id), safe_log(checkpoint), category)
    return {
        "ok": True,
        "artifact_id": artifact_id,
        "category": category,
        "new_content": new_content,
        "diff_summary": diff_summary,
    }
