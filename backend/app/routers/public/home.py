"""公开·首页配置读接口（10.3 /api/content/home）。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.content import Block, Page, PageVersion
from app.schemas.content import PublishedPageOut

router = APIRouter(prefix="/api/content", tags=["content-public"])


@router.get("/home")
async def get_home(db: Annotated[AsyncSession, Depends(get_db)] = None):
    """首页按已发布版本返回区块配置（FR-B06 / FR-B02）。"""
    page = (
        await db.execute(
            select(Page).where(Page.slug == "home", Page.status == "published")
        )
    ).scalar_one_or_none()
    if page is None or page.current_version_id is None:
        raise HTTPException(status_code=404, detail="首页尚未发布")
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
