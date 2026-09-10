"""公开·新闻读接口（FR-F51~F58 / 10.3）。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.enums import NewsCategory, Status
from app.models.content import Article
from app.schemas.content import ArticleOut
from app.schemas.common import PageOut, paginate

router = APIRouter(prefix="/api/news", tags=["news-public"])


@router.get("")
async def list_news(
    category: NewsCategory | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """新闻列表（FR-F51/F52）。"""
    stmt = select(Article).where(Article.status == Status.ONLINE)
    if category is not None:
        stmt = stmt.where(Article.category == category)
    total = (
        await db.execute(
            stmt.with_only_columns(Article.id).order_by(Article.published_at.desc())
        )
    ).scalars().all()
    stmt = (
        stmt.order_by(Article.published_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = list((await db.execute(stmt)).scalars().all())
    items = [ArticleOut.model_validate(a).model_dump(mode="json") for a in rows]
    return paginate(len(total), page, page_size, items).model_dump()


@router.get("/{category}/{slug}")
async def news_detail(
    category: NewsCategory,
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """新闻详情（FR-F53）。"""
    article = (
        await db.execute(
            select(Article).where(
                Article.slug == slug,
                Article.category == category,
                Article.status == Status.ONLINE,
            )
        )
    ).scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="新闻不存在或已下线")
    return ArticleOut.model_validate(article).model_dump(mode="json")
