"""后台·新闻管理（FR-B12~B20）。R2 权限。正文经 XSS 白名单过滤（NFR-18）。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentContentOps
from app.enums import NewsCategory, Status
from app.models.content import Article
from app.schemas.content import ArticleCreate, ArticleOut, ArticleUpdate
from app.services.audit import log_operation
from app.services.sanitize import sanitize_html

router = APIRouter(prefix="/api/admin/news", tags=["admin-news"])


@router.get("", response_model=list[ArticleOut])
async def list_news(
    category: NewsCategory | None = Query(default=None),
    status: Status | None = Query(default=None),
    keyword: str | None = Query(default=None),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentContentOps = None,
):
    stmt = select(Article)
    if category is not None:
        stmt = stmt.where(Article.category == category)
    if status is not None:
        stmt = stmt.where(Article.status == status)
    if keyword:
        stmt = stmt.where(Article.title.like(f"%{keyword}%"))
    stmt = stmt.order_by(Article.created_at.desc())
    rows = list((await db.execute(stmt)).scalars().all())
    return [ArticleOut.model_validate(a).model_dump(mode="json") for a in rows]


@router.post("", response_model=ArticleOut, status_code=201)
async def create_news(
    payload: ArticleCreate,
    current: CurrentContentOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    if (
        await db.execute(select(Article).where(Article.slug == payload.slug))
    ).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="slug 已存在")
    data = payload.model_dump()
    data["content"] = sanitize_html(data.get("content"))
    article = Article(**data)
    db.add(article)
    await db.commit()
    await db.refresh(article)
    await log_operation(db, current, "create", "article", article.id, after=data)
    await db.commit()
    return ArticleOut.model_validate(article).model_dump(mode="json")


@router.get("/{article_id}", response_model=ArticleOut)
async def get_news(
    article_id: int,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentContentOps = None,
):
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="新闻不存在")
    return ArticleOut.model_validate(article).model_dump(mode="json")


@router.put("/{article_id}", response_model=ArticleOut)
async def update_news(
    article_id: int,
    payload: ArticleUpdate,
    current: CurrentContentOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="新闻不存在")
    before = ArticleOut.model_validate(article).model_dump(mode="json")
    for k, v in payload.model_dump(exclude_unset=True).items():
        if k == "content":
            v = sanitize_html(v)
        setattr(article, k, v)
    await db.commit()
    await db.refresh(article)
    await log_operation(
        db, current, "update", "article", article.id,
        before=before, after=ArticleOut.model_validate(article).model_dump(mode="json"),
    )
    await db.commit()
    return ArticleOut.model_validate(article).model_dump(mode="json")


@router.delete("/{article_id}", status_code=204)
async def delete_news(
    article_id: int,
    current: CurrentContentOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="新闻不存在")
    await db.delete(article)
    await db.commit()
    await log_operation(db, current, "delete", "article", article_id)
    await db.commit()
    return None
