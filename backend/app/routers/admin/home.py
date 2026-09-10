"""后台·首页轮播（FULLSCREEN_VISUAL 区块）专用读写接口。

语义：后台改一条轮播 → 生成首页新版本并立即发布 → 前台 GET /api/content/home 读到新帧。
封装了「版本 + 发布」两步，避免管理端自行拼装整页 blocks。
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentContentOps
from app.enums import BlockType, PageStatus
from app.models.content import Block, Page, PageVersion
from app.services.audit import log_operation

router = APIRouter(prefix="/api/admin/home", tags=["admin-home"])

HOME_SLUG = "home"
CAROUSEL = BlockType.FULLSCREEN_VISUAL


class CarouselFrame(BaseModel):
    image: str = ""
    kicker: str = ""
    title: str = ""
    sub: str = ""
    cn: str = ""
    link: str = ""
    active: bool = True


class CarouselIn(BaseModel):
    autoplay: int = 5
    frames: list[CarouselFrame] = []


def _type_val(t: Any) -> str:
    return t.value if hasattr(t, "value") else str(t)


def _layer_of(f: CarouselFrame) -> list[dict]:
    """同时写 layers，兼容 seed 既有结构与旧版前台映射。"""
    out = []
    if f.title:
        out.append({"text": f.title, "style": "brand-wordmark"})
    if f.sub:
        out.append({"text": f.sub, "style": "en-sub"})
    if f.cn:
        out.append({"text": f.cn, "style": "cn-sub"})
    return out


def _raw_frames(frames: list[CarouselFrame]) -> list[dict]:
    return [
        {
            "image": f.image,
            "kicker": f.kicker,
            "title": f.title,
            "sub": f.sub,
            "cn": f.cn,
            "link": f.link,
            "active": bool(f.active),
            "layers": _layer_of(f),
        }
        for f in frames
    ]


def _read_frames(block: Block | None) -> tuple[int, list[dict]]:
    if block is None:
        return 5, []
    cfg = block.config_json or {}
    out = []
    for f in cfg.get("frames") or []:
        layers = f.get("layers") or []
        pick = lambda i: (layers[i].get("text", "") if i < len(layers) else "")
        out.append(
            {
                "image": f.get("image", ""),
                "kicker": f.get("kicker", ""),
                "title": f.get("title") or pick(0),
                "sub": f.get("sub") or pick(1),
                "cn": f.get("cn") or pick(2),
                "link": f.get("link", ""),
                "active": bool(f.get("active", True)),
            }
        )
    return int(cfg.get("autoplay", 5) or 5), out


async def _home_page(db: AsyncSession) -> Page:
    page = (
        await db.execute(select(Page).where(Page.slug == HOME_SLUG))
    ).scalar_one_or_none()
    if page is None:
        raise HTTPException(status_code=404, detail="首页不存在，请先执行 python -m app.seed")
    return page


async def _base_version(db: AsyncSession, page: Page) -> PageVersion | None:
    """当前生效版本优先，否则取最新版本。"""
    if page.current_version_id:
        v = await db.get(PageVersion, page.current_version_id)
        if v:
            return v
    vid = (
        await db.execute(
            select(func.max(PageVersion.id)).where(PageVersion.page_id == page.id)
        )
    ).scalar()
    return await db.get(PageVersion, vid) if vid else None


@router.get("/carousel")
async def get_carousel(
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentContentOps = None,
):
    page = await _home_page(db)
    version = await _base_version(db, page)
    block = None
    if version:
        rows = list(
            (
                await db.execute(
                    select(Block)
                    .where(Block.page_version_id == version.id)
                    .order_by(Block.sort)
                )
            ).scalars().all()
        )
        block = next((b for b in rows if _type_val(b.type) == CAROUSEL.value), None)
    autoplay, frames = _read_frames(block)
    return {
        "page_id": page.id,
        "version_id": version.id if version else None,
        "autoplay": autoplay,
        "frames": frames,
        "updated_at": page.updated_at.isoformat() if page.updated_at else None,
    }


@router.put("/carousel")
async def save_carousel(
    payload: CarouselIn,
    current: CurrentContentOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    page = await _home_page(db)
    base = await _base_version(db, page)
    old_blocks = []
    if base:
        old_blocks = list(
            (
                await db.execute(
                    select(Block)
                    .where(Block.page_version_id == base.id)
                    .order_by(Block.sort)
                )
            ).scalars().all()
        )

    max_no = (
        await db.execute(
            select(func.max(PageVersion.version_no)).where(
                PageVersion.page_id == page.id
            )
        )
    ).scalar() or 0
    version = PageVersion(
        page_id=page.id,
        version_no=max_no + 1,
        created_by=current.id,
        note="更新首页轮播",
    )
    db.add(version)
    await db.flush()

    raw = _raw_frames(payload.frames)
    hit = False
    for b in old_blocks:
        cfg = dict(b.config_json or {})
        if _type_val(b.type) == CAROUSEL.value:
            cfg["autoplay"] = payload.autoplay
            cfg["frames"] = raw
            hit = True
        db.add(
            Block(
                page_version_id=version.id,
                type=b.type,
                config_json=cfg,
                sort=b.sort,
                mobile_visible=b.mobile_visible,
            )
        )
    if not hit:
        db.add(
            Block(
                page_version_id=version.id,
                type=CAROUSEL,
                config_json={"autoplay": payload.autoplay, "frames": raw},
                sort=0,
            )
        )

    page.current_version_id = version.id
    page.status = PageStatus.PUBLISHED
    await db.commit()
    await log_operation(
        db,
        current,
        "publish",
        "page",
        page.id,
        after={"version_no": version.version_no, "frames": len(raw)},
    )
    await db.commit()
    await db.refresh(page)

    return {
        "page_id": page.id,
        "version_id": version.id,
        "version_no": version.version_no,
        "published": True,
        "autoplay": payload.autoplay,
        "frames": [
            {k: f.get(k, "") for k in ("image", "kicker", "title", "sub", "cn", "link")}
            | {"active": f["active"]}
            for f in raw
        ],
        "updated_at": page.updated_at.isoformat() if page.updated_at else None,
    }
