"""公开·全站搜索（FR-F71 / 10.3 /api/search）。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.enums import Status
from app.models.content import Article
from app.models.product import Collection, Item
from app.models.store import Store

router = APIRouter(prefix="/api/search", tags=["search-public"])


@router.get("")
async def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=5, ge=1, le=20),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """对款式/系列/新闻/门店做关键词检索，按类型分组（FR-F71）。"""
    like = f"%{q}%"
    items = list(
        (
            await db.execute(
                select(Item)
                .where(Item.name.like(like), Item.status == Status.ONLINE)
                .limit(limit)
            )
        ).scalars().all()
    )
    collections = list(
        (
            await db.execute(
                select(Collection, Item)
                .join(Item, Collection.item_id == Item.id)
                .where(
                    Collection.name.like(like),
                    Collection.status == Status.ONLINE,
                    # 所属款式已下线时，其系列不应再被检索出来
                    Item.status == Status.ONLINE,
                )
                .limit(limit)
            )
        ).all()
    )
    articles = list(
        (
            await db.execute(
                select(Article)
                .where(Article.title.like(like), Article.status == Status.ONLINE)
                .limit(limit)
            )
        ).scalars().all()
    )
    stores = list(
        (
            await db.execute(
                select(Store)
                .where(Store.name.like(like), Store.status == Status.ONLINE)
                .limit(limit)
            )
        ).scalars().all()
    )
    return {
        "query": q,
        "items": [
            {"item_code": i.item_code, "name": i.name} for i in items
        ],
        "collections": [
            {"name": c.name, "item_code": it.item_code, "category": it.category.value}
            for c, it in collections
        ],
        "news": [{"slug": a.slug, "title": a.title} for a in articles],
        "stores": [{"id": s.id, "name": s.name, "city": s.city} for s in stores],
    }
