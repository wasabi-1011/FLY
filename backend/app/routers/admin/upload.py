"""后台·素材上传：首页轮播图 / 款式主图等图片资源。

保存目录：backend/uploads（相对项目后端根，便于静态挂载为 /uploads）。
返回可直接在 <img src> / CSS background 中使用的相对 URL。
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.config import settings
from app.dependencies import CurrentAnyAdmin

router = APIRouter(prefix="/api/admin/upload", tags=["admin-upload"])

# backend/app/routers/admin/upload.py -> parents[3] = backend/
BACKEND_DIR = Path(__file__).resolve().parents[3]
UPLOAD_DIR = BACKEND_DIR / "uploads"

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_CT = {"image/jpeg", "image/png", "image/webp", "image/gif"}
EXT_BY_CT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


@router.post("", status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    current: CurrentAnyAdmin = None,
):
    """上传一张图片，返回 {"url": "/uploads/xxx.jpg"}。

    权限：任意已登录后台账号（SUPER_ADMIN / CONTENT_OPS / MERCH_STORE_OPS）。
    原先只放给内容运营，导致门店商品运营（R3）维护款式主图时上传 403。
    """
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        ext = EXT_BY_CT.get((file.content_type or "").lower(), "")
    if not ext:
        raise HTTPException(
            status_code=415, detail="仅支持 jpg / png / webp / gif 格式"
        )
    if (file.content_type or "").lower() not in ALLOWED_CT and ext not in ALLOWED_EXT:
        raise HTTPException(status_code=415, detail="文件类型不受支持")

    body = await file.read()
    max_bytes = settings.UPLOAD_MAX_MB * 1024 * 1024
    if not body:
        raise HTTPException(status_code=400, detail="空文件")
    if len(body) > max_bytes:
        raise HTTPException(
            status_code=413, detail=f"文件超过 {settings.UPLOAD_MAX_MB}MB 上限"
        )

    name = f"{uuid.uuid4().hex}{ext}"
    (UPLOAD_DIR / name).write_bytes(body)
    return {
        "url": f"/uploads/{name}",
        "filename": file.filename,
        "size": len(body),
        "uploaded_by": getattr(current, "username", None),
    }
