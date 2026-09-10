"""公开·产品中心读接口（FR-F21~F30 / 10.3）。

路由顺序注意：静态段 /products/hot 必须声明在 /products/{category} 之前，
否则 hot 会被当成品类名解析（PRD 5.3 路由优先级）。
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.enums import Category, Status
from app.models.product import Collection, Item
from app.schemas.product import CollectionOut, ItemOut

router = APIRouter(prefix="/api/products", tags=["products-public"])


def _parse_category(value: str) -> Category:
    try:
        return Category(value)
    except ValueError:
        raise HTTPException(status_code=404, detail="品类不存在")


async def _attach_category(db: AsyncSession, items: list[Item]) -> list[Item]:
    for it in items:
        col = await db.get(Collection, it.collection_id)
        it.category = col.category if col else None  # type: ignore[attr-defined]
    return items


async def _collection_with_count(db: AsyncSession, c: Collection) -> dict:
    cnt = (
        await db.execute(
            select(func.count(Item.id)).where(
                Item.collection_id == c.id, Item.status == Status.ONLINE
            )
        )
    ).scalar() or 0
    d = CollectionOut.model_validate(c).model_dump()
    d["item_count"] = cnt
    return d


@router.get("/hot")
async def list_hot(
    category: Category | None = Query(default=None),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """热门推荐页（FR-F23）。is_hot 纯人工标记，绝不按销量。"""
    stmt = select(Item).where(Item.is_hot == True, Item.status == Status.ONLINE)
    if category is not None:
        stmt = stmt.join(Collection).where(Collection.category == category)
    stmt = stmt.order_by(Item.hot_sort.asc(), Item.sort_weight.desc())
    items = list((await db.execute(stmt)).scalars().all())
    await _attach_category(db, items)
    return [ItemOut.model_validate(i).model_dump() for i in items]


@router.get("/{category}")
async def category_page(
    category: str,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """品类页：系列墙 + 该品类热门款式（FR-F21/F22）。"""
    cat = _parse_category(category)
    cols = list(
        (
            await db.execute(
                select(Collection)
                .where(Collection.category == cat, Collection.status == Status.ONLINE)
                .order_by(Collection.sort_weight.desc(), Collection.published_at.desc())
            )
        ).scalars().all()
    )
    hot = list(
        (
            await db.execute(
                select(Item)
                .join(Collection)
                .where(
                    Collection.category == cat,
                    Item.is_hot == True,
                    Item.status == Status.ONLINE,
                )
                .order_by(Item.hot_sort.asc())
            )
        ).scalars().all()
    )
    await _attach_category(db, hot)
    return {
        "category": cat.value,
        "collections": [await _collection_with_count(db, c) for c in cols],
        "hot_items": [ItemOut.model_validate(i).model_dump() for i in hot],
    }


@router.get("/{category}/{collection_slug}")
async def collection_detail(
    category: str,
    collection_slug: str,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """系列详情（FR-F25）。"""
    cat = _parse_category(category)
    col = (
        await db.execute(
            select(Collection).where(
                Collection.slug == collection_slug,
                Collection.category == cat,
                Collection.status == Status.ONLINE,
            )
        )
    ).scalar_one_or_none()
    if col is None:
        raise HTTPException(status_code=404, detail="系列不存在或已下线")
    items = list(
        (
            await db.execute(
                select(Item)
                .where(Item.collection_id == col.id, Item.status == Status.ONLINE)
                .order_by(Item.sort_weight.desc())
            )
        ).scalars().all()
    )
    await _attach_category(db, items)
    return {
        "collection": CollectionOut.model_validate(col).model_dump(),
        "items": [ItemOut.model_validate(i).model_dump() for i in items],
    }


@router.get("/{category}/{collection_slug}/{item_code}")
async def item_detail(
    category: str,
    collection_slug: str,
    item_code: str,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """款式详情（FR-F27）。前台绝不返回价格/库存/尺码。"""
    cat = _parse_category(category)
    col = (
        await db.execute(
            select(Collection).where(
                Collection.slug == collection_slug, Collection.category == cat
            )
        )
    ).scalar_one_or_none()
    if col is None:
        raise HTTPException(status_code=404, detail="系列不存在")
    item = (
        await db.execute(
            select(Item).where(
                Item.item_code == item_code,
                Item.collection_id == col.id,
                Item.status == Status.ONLINE,
            )
        )
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="款式不存在或已下线")
    item.category = col.category  # type: ignore[attr-defined]
    return ItemOut.model_validate(item).model_dump()
