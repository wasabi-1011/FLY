"""后台·款式管理（FR-B22~B24 / FR-B26 / FR-B29）。R3 权限。

层级 v2.3：款式 = 服装主体，自带品类；系列挂在款式下（选填）。
v2.3 起款号（item_code）可留空，由后端按「品类前缀 + 三位序号」自动生成。
"""
from __future__ import annotations

import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import CurrentMerchStoreOps
from app.enums import Category, Status
from app.models.product import Collection, Item
from app.schemas.product import CollectionOut, ItemCreate, ItemOut, ItemUpdate
from app.services.audit import log_operation

router = APIRouter(prefix="/api/admin/items", tags=["admin-items"])

# 款号自动生成：品类 → 前缀。与既有种子数据（CO-SW001 女 / CO-MN002 男 / CO-KD005 童）保持一致。
CODE_PREFIX: dict[Category, str] = {
    Category.WOMEN: "SW",
    Category.MEN: "MN",
    Category.KIDS: "KD",
}


async def _code_exists(db: AsyncSession, code: str) -> bool:
    return (
        await db.execute(select(Item.id).where(Item.item_code == code))
    ).scalar_one_or_none() is not None


async def _next_item_code(db: AsyncSession, category: Category) -> str:
    """下一个可用款号：``CO-<前缀><三位序号>``。

    从同品类已有款号的**最大序号 +1** 起，若该位已被占用则继续向后探测空位
    （款号是 UNIQUE，删除中间的款后序号不该被复用）。
    """
    pfx = CODE_PREFIX.get(category, "XX")
    rows = (
        await db.execute(select(Item.item_code).where(Item.item_code.like(f"CO-{pfx}%")))
    ).scalars().all()
    used: set[int] = set()
    mx = 0
    for c in rows:
        m = re.match(rf"^CO-{pfx}(\d+)$", c or "")
        if m:
            used.add(int(m.group(1)))
            mx = max(mx, int(m.group(1)))
    n = mx + 1
    while n in used:
        n += 1
    return f"CO-{pfx}{n:03d}"


def _item_out(it: Item) -> dict:
    """款式出参统一入口。

    ItemOut 的字段名是 ``series``，而 ORM 关系名是 ``collections``，二者不一致，
    直接 model_validate 拿不到系列，会恒为空数组。这里手动填充一次。
    只在关系已加载（selectinload）时从 ``__dict__`` 读取，绝不触发异步懒加载。
    """
    d = ItemOut.model_validate(it).model_dump()
    cols = it.__dict__.get("collections") or []
    d["series"] = [CollectionOut.model_validate(c).model_dump() for c in cols]
    return d


@router.get("", response_model=list[ItemOut])
async def list_items(
    category: Category | None = Query(default=None, description="按品类过滤"),
    status: Status | None = Query(default=None),
    is_hot: bool | None = Query(default=None),
    keyword: str | None = Query(default=None, description="匹配款名或款号"),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentMerchStoreOps = None,
):
    stmt = select(Item).options(selectinload(Item.collections))
    if category is not None:
        stmt = stmt.where(Item.category == category)
    if status is not None:
        stmt = stmt.where(Item.status == status)
    if is_hot is not None:
        stmt = stmt.where(Item.is_hot == is_hot)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(Item.name.like(like), Item.item_code.like(like)))
    stmt = stmt.order_by(Item.sort_weight.desc(), Item.id.asc())
    items = list((await db.execute(stmt)).scalars().all())
    return [_item_out(i) for i in items]


@router.post("", response_model=ItemOut, status_code=201)
async def create_item(
    payload: ItemCreate,
    current: CurrentMerchStoreOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    data = payload.model_dump()
    code = (data.pop("item_code", None) or "").strip()
    if code:
        if await _code_exists(db, code):
            raise HTTPException(status_code=409, detail="款号已存在")
    else:
        # 款号留空 → 自动生成（已内含「向后探测空位」逻辑）
        code = await _next_item_code(db, payload.category)
    item = Item(**data, item_code=code)
    db.add(item)
    try:
        await db.commit()
    except IntegrityError:
        # 极端并发下两次请求算出同一个款号 → 干净地报 409，而不是 500
        await db.rollback()
        raise HTTPException(status_code=409, detail="款号已存在，请重试")
    await db.refresh(item)
    await log_operation(db, current, "create", "item", item.id, after={**payload.model_dump(), "item_code": code})
    await db.commit()
    return _item_out(item)


@router.get("/{item_id}", response_model=ItemOut)
async def get_item(
    item_id: int,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentMerchStoreOps = None,
):
    item = (
        await db.execute(
            select(Item).options(selectinload(Item.collections)).where(Item.id == item_id)
        )
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="款式不存在")
    return _item_out(item)


@router.put("/{item_id}", response_model=ItemOut)
async def update_item(
    item_id: int,
    payload: ItemUpdate,
    current: CurrentMerchStoreOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    item = (
        await db.execute(
            select(Item).options(selectinload(Item.collections)).where(Item.id == item_id)
        )
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="款式不存在")
    before = _item_out(item)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    await db.commit()
    await db.refresh(item)
    item = (
        await db.execute(
            select(Item).options(selectinload(Item.collections)).where(Item.id == item_id)
        )
    ).scalar_one_or_none()
    await log_operation(
        db, current, "update", "item", item.id,
        before=before, after=_item_out(item),
    )
    await db.commit()
    return _item_out(item)


@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: int,
    current: CurrentMerchStoreOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    item = await db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="款式不存在")
    # 删除保护（v2.2）：款式下仍有系列时拒绝删除，避免 CASCADE 把系列一并静默删掉。
    series_count = (
        await db.execute(
            select(func.count(Collection.id)).where(Collection.item_id == item_id)
        )
    ).scalar() or 0
    if series_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"该款式下还有 {series_count} 个系列，请先清空或转移到其他款式后再删除",
        )
    await db.delete(item)
    await db.commit()
    await log_operation(db, current, "delete", "item", item_id)
    await db.commit()
    return None
