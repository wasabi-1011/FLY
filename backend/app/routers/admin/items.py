"""后台·款式管理（FR-B22 / FR-B23 / FR-B24 / FR-B26 / FR-B29）。R3 权限。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentMerchStoreOps
from app.enums import Status
from app.models.product import Collection, Item
from app.schemas.product import ItemCreate, ItemOut, ItemUpdate
from app.services.audit import log_operation

router = APIRouter(prefix="/api/admin/items", tags=["admin-items"])


@router.get("", response_model=list[ItemOut])
async def list_items(
    collection_id: int | None = Query(default=None),
    is_hot: bool | None = Query(default=None),
    keyword: str | None = Query(default=None),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentMerchStoreOps = None,
):
    stmt = select(Item)
    if collection_id is not None:
        stmt = stmt.where(Item.collection_id == collection_id)
    if is_hot is not None:
        stmt = stmt.where(Item.is_hot == is_hot)
    if keyword:
        stmt = stmt.where(Item.name.like(f"%{keyword}%"))
    stmt = stmt.order_by(Item.sort_weight.desc())
    items = list((await db.execute(stmt)).scalars().all())
    for it in items:
        col = await db.get(Collection, it.collection_id)
        it.category = col.category if col else None  # type: ignore[attr-defined]
    return [ItemOut.model_validate(i).model_dump() for i in items]


@router.post("", response_model=ItemOut, status_code=201)
async def create_item(
    payload: ItemCreate,
    current: CurrentMerchStoreOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    if not (
        await db.execute(
            select(Collection).where(Collection.id == payload.collection_id)
        )
    ).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="所属系列不存在")
    if (
        await db.execute(
            select(Item).where(Item.item_code == payload.item_code)
        )
    ).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="款号已存在")
    item = Item(**payload.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    col = await db.get(Collection, item.collection_id)
    item.category = col.category if col else None  # type: ignore[attr-defined]
    await log_operation(db, current, "create", "item", item.id, after=payload.model_dump())
    await db.commit()
    return ItemOut.model_validate(item).model_dump()


@router.get("/{item_id}", response_model=ItemOut)
async def get_item(
    item_id: int,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentMerchStoreOps = None,
):
    item = await db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="款式不存在")
    col = await db.get(Collection, item.collection_id)
    item.category = col.category if col else None  # type: ignore[attr-defined]
    return ItemOut.model_validate(item).model_dump()


@router.put("/{item_id}", response_model=ItemOut)
async def update_item(
    item_id: int,
    payload: ItemUpdate,
    current: CurrentMerchStoreOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    item = await db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="款式不存在")
    before = ItemOut.model_validate(item).model_dump()
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    # 跨系列移动时品类随之变更（FR-B24）
    await db.commit()
    await db.refresh(item)
    col = await db.get(Collection, item.collection_id)
    item.category = col.category if col else None  # type: ignore[attr-defined]
    await log_operation(
        db, current, "update", "item", item.id,
        before=before, after=ItemOut.model_validate(item).model_dump(),
    )
    await db.commit()
    return ItemOut.model_validate(item).model_dump()


@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: int,
    current: CurrentMerchStoreOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    item = await db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="款式不存在")
    await db.delete(item)
    await db.commit()
    await log_operation(db, current, "delete", "item", item_id)
    await db.commit()
    return None
