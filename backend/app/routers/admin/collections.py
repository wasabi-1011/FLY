"""后台·系列管理（FR-B21 / FR-B25 / FR-B26）。R3 权限。

层级 v2.2 起：系列挂在款式下（选填），用 item_id 关联；品类由所属款式继承，不再单独存储。
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentMerchStoreOps
from app.enums import Status
from app.models.product import Collection, Item
from app.schemas.product import CollectionCreate, CollectionOut, CollectionUpdate
from app.services.audit import log_operation

router = APIRouter(prefix="/api/admin/collections", tags=["admin-collections"])


def _out(col: Collection, item: Item | None = None) -> dict:
    d = CollectionOut.model_validate(col).model_dump()
    if item is not None:
        d["item_code"] = item.item_code
        d["item_name"] = item.name
    return d


@router.get("", response_model=list[CollectionOut])
async def list_collections(
    item_id: int | None = Query(default=None, description="按所属款式过滤"),
    status: Status | None = Query(default=None),
    keyword: str | None = Query(default=None),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentMerchStoreOps = None,
):
    stmt = select(Collection, Item).join(Item, Collection.item_id == Item.id)
    if item_id is not None:
        stmt = stmt.where(Collection.item_id == item_id)
    if status is not None:
        stmt = stmt.where(Collection.status == status)
    if keyword:
        stmt = stmt.where(Collection.name.like(f"%{keyword}%"))
    stmt = stmt.order_by(Collection.item_id.asc(), Collection.id.asc())
    rows = (await db.execute(stmt)).all()
    return [_out(col, item) for col, item in rows]


@router.post("", response_model=CollectionOut, status_code=201)
async def create_collection(
    payload: CollectionCreate,
    current: CurrentMerchStoreOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    item = await db.get(Item, payload.item_id)
    if not item:
        raise HTTPException(status_code=400, detail="所属款式不存在")
    col = Collection(**payload.model_dump())
    db.add(col)
    await db.commit()
    await db.refresh(col)
    await log_operation(db, current, "create", "collection", col.id, after=payload.model_dump())
    await db.commit()
    return _out(col, item)


@router.get("/{col_id}", response_model=CollectionOut)
async def get_collection(
    col_id: int,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentMerchStoreOps = None,
):
    col = await db.get(Collection, col_id)
    if not col:
        raise HTTPException(status_code=404, detail="系列不存在")
    return _out(col, await db.get(Item, col.item_id))


@router.put("/{col_id}", response_model=CollectionOut)
async def update_collection(
    col_id: int,
    payload: CollectionUpdate,
    current: CurrentMerchStoreOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    col = await db.get(Collection, col_id)
    if not col:
        raise HTTPException(status_code=404, detail="系列不存在")
    before = CollectionOut.model_validate(col).model_dump()
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(col, k, v)
    await db.commit()
    await db.refresh(col)
    await log_operation(
        db, current, "update", "collection", col.id,
        before=before, after=CollectionOut.model_validate(col).model_dump(),
    )
    await db.commit()
    return _out(col, await db.get(Item, col.item_id))


@router.delete("/{col_id}", status_code=204)
async def delete_collection(
    col_id: int,
    current: CurrentMerchStoreOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    col = await db.get(Collection, col_id)
    if not col:
        raise HTTPException(status_code=404, detail="系列不存在")
    await db.delete(col)
    await db.commit()
    await log_operation(db, current, "delete", "collection", col_id)
    await db.commit()
    return None
