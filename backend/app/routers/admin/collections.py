"""后台·系列管理（FR-B21 / FR-B25 / FR-B26 / FR-B28）。R3 权限。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentMerchStoreOps
from app.enums import Category, Status
from app.models.admin import AdminUser
from app.models.product import Collection
from app.schemas.product import CollectionCreate, CollectionOut, CollectionUpdate
from app.services.audit import log_operation

router = APIRouter(prefix="/api/admin/collections", tags=["admin-collections"])


@router.get("", response_model=list[CollectionOut])
async def list_collections(
    category: Category | None = Query(default=None),
    status: Status | None = Query(default=None),
    keyword: str | None = Query(default=None),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentMerchStoreOps = None,
):
    stmt = select(Collection)
    if category is not None:
        stmt = stmt.where(Collection.category == category)
    if status is not None:
        stmt = stmt.where(Collection.status == status)
    if keyword:
        stmt = stmt.where(Collection.name.like(f"%{keyword}%"))
    stmt = stmt.order_by(Collection.sort_weight.desc())
    rows = list((await db.execute(stmt)).scalars().all())
    return [CollectionOut.model_validate(c).model_dump() for c in rows]


@router.post("", response_model=CollectionOut, status_code=201)
async def create_collection(
    payload: CollectionCreate,
    current: CurrentMerchStoreOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    if (
        await db.execute(
            select(Collection).where(Collection.slug == payload.slug)
        )
    ).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="slug 已存在")
    col = Collection(**payload.model_dump())
    db.add(col)
    await db.commit()
    await db.refresh(col)
    await log_operation(db, current, "create", "collection", col.id, after=payload.model_dump())
    await db.commit()
    return CollectionOut.model_validate(col).model_dump()


@router.get("/{col_id}", response_model=CollectionOut)
async def get_collection(
    col_id: int,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentMerchStoreOps = None,
):
    col = await db.get(Collection, col_id)
    if not col:
        raise HTTPException(status_code=404, detail="系列不存在")
    return CollectionOut.model_validate(col).model_dump()


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
    return CollectionOut.model_validate(col).model_dump()


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
