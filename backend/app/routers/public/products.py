"""公开·产品中心读接口（FR-F21~F30 / 10.3）。

层级 v2.2 起：品类 → 款式 → 系列。
本接口按「品类」返回款式；每个款式自带其系列列表（选填）。

路由顺序注意：静态段 /products/hot 必须声明在 /products/{category} 之前，
否则 hot 会被当成品类名解析（PRD 5.3 路由优先级）。
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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


def _item_dict(it: Item) -> dict:
    """款式 + 其下系列（选填）一起返回，前台一次取全。

    只在关系已加载（selectinload）时从 ``__dict__`` 读取，绝不触发异步懒加载 ——
    否则将来有人新增调用点却忘了 selectinload，会直接 500。
    """
    d = ItemOut.model_validate(it).model_dump()
    d["series"] = [
        CollectionOut.model_validate(c).model_dump()
        for c in (it.__dict__.get("collections") or [])
    ]
    return d


@router.get("/hot")
async def list_hot(
    category: Category | None = Query(default=None),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """热门推荐页（FR-F23）。is_hot 纯人工标记，绝不按销量。"""
    stmt = (
        select(Item)
        .options(selectinload(Item.collections))
        .where(Item.is_hot == True, Item.status == Status.ONLINE)
    )
    if category is not None:
        stmt = stmt.where(Item.category == category)
    stmt = stmt.order_by(Item.hot_sort.asc(), Item.sort_weight.desc())
    items = list((await db.execute(stmt)).scalars().all())
    return [_item_dict(i) for i in items]


@router.get("/{category}")
async def category_page(
    category: str,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """品类页：该品类下的全部在线款式（每个款式带出它的系列）。"""
    cat = _parse_category(category)
    stmt = (
        select(Item)
        .options(selectinload(Item.collections))
        .where(Item.category == cat, Item.status == Status.ONLINE)
        .order_by(Item.sort_weight.desc(), Item.id.asc())
    )
    items = list((await db.execute(stmt)).scalars().all())
    hot = [i for i in items if i.is_hot]
    return {
        "category": cat.value,
        "items": [_item_dict(i) for i in items],
        "hot_items": [_item_dict(i) for i in hot],
    }


@router.get("/{category}/{item_code}")
async def item_detail(
    category: str,
    item_code: str,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """款式详情（FR-F27）。前台绝不返回价格/库存/尺码。"""
    cat = _parse_category(category)
    item = (
        await db.execute(
            select(Item)
            .options(selectinload(Item.collections))
            .where(
                Item.item_code == item_code,
                Item.category == cat,
                Item.status == Status.ONLINE,
            )
        )
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="款式不存在或已下线")
    return _item_dict(item)
