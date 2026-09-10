"""公开·固定页 / 专题页读接口（FR-F88 / FR-B55 / 10.3 /api/pages/{*slug}）。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.content import Block, Page, PageVersion
from app.schemas.content import PublishedPageOut

router = APIRouter(prefix="/api/pages", tags=["pages-public"])


@router.get("/{full_path:path}")
async def get_page(
    full_path: str,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """固定页（about/*、join/*）与专题页（campaign/*）按 slug 读取已发布版本。"""
    page = (
        await db.execute(
            select(Page).where(Page.slug == full_path, Page.status == "published")
        )
    ).scalar_one_or_none()
    if page is None or page.current_version_id is None:
        raise HTTPException(status_code=404, detail="页面不存在或已下线")
    version = await db.get(PageVersion, page.current_version_id)
    blocks = (
        list(
            (
                await db.execute(
                    select(Block)
                    .where(Block.page_version_id == version.id)
                    .order_by(Block.sort)
                )
            ).scalars().all()
        )
        if version
        else []
    )
    return PublishedPageOut(
        slug=page.slug,
        title=page.title,
        page_type=page.page_type,
        blocks=[b for b in blocks],
    ).model_dump(mode="json")
