"""后台·门店管理 + 库存导入/查询（FR-B31~B37 / FR-B41~B47）。R3 权限。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentMerchStoreOps
from app.enums import Status, StoreType
from app.models.product import Item
from app.models.store import Store, StoreStock
from app.schemas.store import StoreCreate, StoreOut, StoreStockCreate, StoreStockOut
from app.services.audit import log_operation

router = APIRouter(prefix="/api/admin/stores", tags=["admin-stores"])


@router.get("", response_model=list[StoreOut])
async def list_stores(
    city: str | None = Query(default=None),
    store_type: StoreType | None = Query(default=None),
    status: Status | None = Query(default=None),
    keyword: str | None = Query(default=None),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentMerchStoreOps = None,
):
    stmt = select(Store)
    if city:
        stmt = stmt.where(Store.city == city)
    if store_type:
        stmt = stmt.where(Store.store_type == store_type)
    if status is not None:
        stmt = stmt.where(Store.status == status)
    if keyword:
        stmt = stmt.where(Store.name.like(f"%{keyword}%"))
    rows = list((await db.execute(stmt)).scalars().all())
    return [StoreOut.model_validate(s).model_dump() for s in rows]


@router.post("", response_model=StoreOut, status_code=201)
async def create_store(
    payload: StoreCreate,
    current: CurrentMerchStoreOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    store = Store(**payload.model_dump())
    db.add(store)
    await db.commit()
    await db.refresh(store)
    await log_operation(db, current, "create", "store", store.id, after=payload.model_dump())
    await db.commit()
    return StoreOut.model_validate(store).model_dump()


@router.get("/{store_id}", response_model=StoreOut)
async def get_store(
    store_id: int,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentMerchStoreOps = None,
):
    store = await db.get(Store, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")
    return StoreOut.model_validate(store).model_dump()


@router.put("/{store_id}", response_model=StoreOut)
async def update_store(
    store_id: int,
    payload: StoreCreate,
    current: CurrentMerchStoreOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    store = await db.get(Store, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")
    for k, v in payload.model_dump().items():
        setattr(store, k, v)
    await db.commit()
    await db.refresh(store)
    await log_operation(db, current, "update", "store", store.id)
    await db.commit()
    return StoreOut.model_validate(store).model_dump()


@router.delete("/{store_id}", status_code=204)
async def delete_store(
    store_id: int,
    current: CurrentMerchStoreOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    store = await db.get(Store, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")
    await db.delete(store)
    await db.commit()
    await log_operation(db, current, "delete", "store", store_id)
    await db.commit()
    return None


# ---------------- 库存（内部工具，FR-B41~B47） ----------------

@router.get("/stock/list", response_model=list[StoreStockOut])
async def list_stock(
    item_code: str | None = Query(default=None),
    store_id: int | None = Query(default=None),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentMerchStoreOps = None,
):
    stmt = select(StoreStock)
    if item_code:
        stmt = stmt.where(StoreStock.item_code == item_code)
    if store_id:
        stmt = stmt.where(StoreStock.store_id == store_id)
    rows = list((await db.execute(stmt)).scalars().all())
    return [StoreStockOut.model_validate(r).model_dump(mode="json") for r in rows]


@router.post("/stock/import", response_model=dict)
async def import_stock(
    payload: list[StoreStockCreate],
    current: CurrentMerchStoreOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Excel 批量导入：按 (store_id, item_code) 唯一键 upsert（FR-B43/B47）。

    任一行的门店或款号不存在则收集错误并指出行号，不静默失败。
    """
    updated = 0
    errors: list[dict] = []
    for idx, row in enumerate(payload, start=1):
        store = await db.get(Store, row.store_id)
        item = (
            await db.execute(
                select(Item).where(Item.item_code == row.item_code)
            )
        ).scalar_one_or_none()
        if store is None or item is None:
            errors.append(
                {
                    "row": idx,
                    "store_id": row.store_id,
                    "item_code": row.item_code,
                    "message": (
                        "门店不存在" if store is None else "款号不存在"
                    ),
                }
            )
            continue
        existing = (
            await db.execute(
                select(StoreStock).where(
                    StoreStock.store_id == row.store_id,
                    StoreStock.item_code == row.item_code,
                )
            )
        ).scalar_one_or_none()
        if existing:
            existing.quantity = row.quantity
            existing.updated_at = __import__("datetime").datetime.utcnow()
            updated += 1
        else:
            db.add(
                StoreStock(
                    store_id=row.store_id,
                    item_code=row.item_code,
                    quantity=row.quantity,
                )
            )
            updated += 1
    await db.commit()
    await log_operation(
        db, current, "import", "store_stock",
        after={"rows": len(payload), "updated": updated, "errors": len(errors)},
    )
    await db.commit()
    return {
        "received": len(payload),
        "updated_or_inserted": updated,
        "errors": errors,
    }
