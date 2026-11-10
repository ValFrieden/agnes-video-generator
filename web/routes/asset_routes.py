"""web.routes.asset_routes — 工作区角色与风格资产库（跨任务复用）。"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from core.async_io import write_bytes
from core.config import get_working_dir
from core.path_security import UnsafePathError, safe_join

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/assets", tags=["assets"])

_ALLOWED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
_MAX_ASSET_BYTES = 20 * 1024 * 1024


def _assets_dir() -> str:
    d = os.path.join(get_working_dir(), "_asset_library")
    os.makedirs(d, exist_ok=True)
    return d


def _manifest_path() -> str:
    return os.path.join(_assets_dir(), "library.json")


def _load_library() -> list[dict]:
    path = _manifest_path()
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_library(items: list[dict]) -> None:
    path = _manifest_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


@router.get("")
async def list_assets():
    """列出当前工作区已保存的角色/风格资产。"""
    items = _load_library()
    assets_dir = _assets_dir()
    valid: list[dict] = []
    for item in items:
        img_name = item.get("image_file", "")
        has_img = bool(img_name and os.path.isfile(os.path.join(assets_dir, img_name)))
        valid.append({
            **item,
            "image_url": f"/api/assets/{item['id']}/image" if has_img else None,
        })
    return {"ok": True, "assets": valid}


@router.post("")
async def create_asset(
    name: str = Form(...),
    kind: str = Form("character"),
    prompt: str = Form(""),
    continuity_locks: str = Form(""),
    image: Optional[UploadFile] = File(None),
):
    """保存可复用的角色卡/风格参考图与连续性锚点提示词。"""
    clean_name = name.strip()
    if not clean_name:
        raise HTTPException(status_code=422, detail="Asset name is required")
    if kind not in ("character", "style", "prop"):
        kind = "character"

    asset_id = uuid.uuid4().hex[:10]
    assets_dir = _assets_dir()
    image_file = ""

    if image and image.filename:
        ext = (os.path.splitext(image.filename)[1] or ".png").lower()
        if ext not in _ALLOWED_IMAGE_EXTS:
            ext = ".png"
        data = await image.read(_MAX_ASSET_BYTES + 1)
        if len(data) > _MAX_ASSET_BYTES:
            raise HTTPException(status_code=413, detail="Image too large (max 20MB)")
        image_file = f"{asset_id}{ext}"
        try:
            dest = safe_join(assets_dir, image_file)
        except UnsafePathError:
            raise HTTPException(status_code=400, detail="Invalid asset path")
        await write_bytes(dest, data)

    entry = {
        "id": asset_id,
        "name": clean_name,
        "kind": kind,
        "prompt": prompt.strip(),
        "continuity_locks": continuity_locks.strip(),
        "image_file": image_file,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    items = _load_library()
    items.insert(0, entry)
    _save_library(items)

    return {
        "ok": True,
        "asset": {
            **entry,
            "image_url": f"/api/assets/{asset_id}/image" if image_file else None,
        },
    }


@router.get("/{asset_id}/image")
async def get_asset_image(asset_id: str):
    """获取资产库参考图片。"""
    items = _load_library()
    item = next((x for x in items if x.get("id") == asset_id), None)
    if not item or not item.get("image_file"):
        raise HTTPException(status_code=404, detail="Asset image not found")
    try:
        path = safe_join(_assets_dir(), item["image_file"])
    except UnsafePathError:
        raise HTTPException(status_code=404, detail="Asset image not found")
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Asset image not found")
    return FileResponse(path)


@router.delete("/{asset_id}")
async def delete_asset(asset_id: str):
    """删除资产库条目及关联图片。"""
    items = _load_library()
    target = next((x for x in items if x.get("id") == asset_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Asset not found")
    if target.get("image_file"):
        try:
            path = safe_join(_assets_dir(), target["image_file"])
            if os.path.isfile(path):
                os.remove(path)
        except Exception as e:
            logger.warning("[Assets] Failed to remove image for %s: %s", asset_id, e)
    items = [x for x in items if x.get("id") != asset_id]
    _save_library(items)
    return {"ok": True}
