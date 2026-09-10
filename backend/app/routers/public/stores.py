"""公开·门店查询读接口（FR-F31~F45 / 10.3）。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.enums import Status, StoreType
from app.models.store import Store, StoreStock
from app.schemas.store import StoreAvailability, StoreOut

router = APIRouter(prefix="/api/stores", tags=["stores-public"])


@router.get("/cities")
async def list_cities(db: Annotated[AsyncSession, Depends(get_db)] = None):
    """有门店的城市 + 门店数量（供筛选器与热门城市标签初始化，FR-F32 / /api/stores/cities）。"""
    rows = (
        await db.execute(
            select(Store.city, func.count(Store.id))
            .where(Store.status == Status.ONLINE)
            .group_by(Store.city)
            .order_by(func.count(Store.id).desc())
        )
    ).all()
    return [{"city": city, "store_count": cnt} for city, cnt in rows]


@router.get("")
async def list_stores(
    city: str | None = Query(default=None),
    store_type: StoreType | None = Query(default=None),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """门店列表 + 地图点位（FR-F31/F33）。"""
    stmt = select(Store).where(Store.status == Status.ONLINE)
    if city:
        stmt = stmt.where(Store.city == city)
    if store_type:
        stmt = stmt.where(Store.store_type == store_type)
    stores = list((await db.execute(stmt)).scalars().all())
    return [StoreOut.model_validate(s).model_dump() for s in stores]


@router.get("/availability")
async def availability(
    item_code: str = Query(...),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """某款式有货城市（仅城市名，不返回数量，FR-F28 / FR-B41）。"""
    rows = (
        await db.execute(
            select(Store.city)
            .join(StoreStock, StoreStock.store_id == Store.id)
            .where(
                StoreStock.item_code == item_code,
                StoreStock.quantity > 0,
                Store.status == Status.ONLINE,
            )
            .distinct()
        )
    ).all()
    cities = sorted({r[0] for r in rows})
    return StoreAvailability(item_code=item_code, cities=cities).model_dump()


@router.get("/{store_id}")
async def store_detail(
    store_id: int,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """门店详情（FR-F34），必须有独立可收录 URL。"""
    store = await db.get(Store, store_id)
    if store is None or store.status != Status.ONLINE:
        raise HTTPException(status_code=404, detail="门店不存在或已下线")
    return StoreOut.model_validate(store).model_dump()
