"""后台·门店管理 + 库存导入/查询（FR-B31~B37 / FR-B41~B47）。R3 权限。

v2.6 变更：
1. `PUT /{store_id}` 入参由 `StoreCreate`（全量覆盖）改为 `StoreUpdate`（部分更新）——
   原实现会把未提交的 phone/business_hours/images 等字段重置为 None，且 status 被
   默认值 ONLINE 顶掉（**编辑一家下线门店会把它悄悄改回在线**）。
2. 新增 `POST /geocode`：地址 → GCJ-02 坐标（服务端 Key，仅后台录入用）。
3. 列表 `keyword` 扩展为同时匹配 名称 / 城市 / 地址；补 `limit` / `offset` 分页；
   出参新增 `stock_count`（删除前提示连带清除的库存条数）。
4. 路由顺序：`/geocode` 与 `/stock/*` 必须定义在 `/{store_id}` **之前**，
   否则会被 `store_id: int` 抢先匹配并返回 422（原 `/stock/*` 就踩了这个坑）。
"""
from __future__ import annotations

import asyncio
import json
import urllib.parse
import urllib.request
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import CurrentMerchStoreOps
from app.enums import Status, StoreType
from app.models.product import Item
from app.models.store import Store, StoreStock
from app.schemas.store import (
    StoreCreate,
    StoreGeocodeIn,
    StoreGeocodeOut,
    StoreOut,
    StoreStockCreate,
    StoreStockOut,
    StoreUpdate,
)
from app.services.audit import log_operation

router = APIRouter(prefix="/api/admin/stores", tags=["admin-stores"])

# 编辑时不允许置空的必填字段（StoreUpdate 全字段可选，需在应用层守住）
_REQUIRED_NOT_NULL = ("name", "province", "city", "address", "lng", "lat")


@router.get("", response_model=list[StoreOut])
async def list_stores(
    city: str | None = Query(default=None),
    store_type: StoreType | None = Query(default=None),
    status: Status | None = Query(default=None),
    keyword: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentMerchStoreOps = None,
):
    # 连带统计库存条数：供前端删除前提示「会连带清除 N 条库存」
    stmt = (
        select(Store, func.count(StoreStock.id))
        .join(StoreStock, StoreStock.store_id == Store.id, isouter=True)
        .group_by(Store.id)
    )
    if city:
        stmt = stmt.where(Store.city == city)
    if store_type:
        stmt = stmt.where(Store.store_type == store_type)
    if status is not None:
        stmt = stmt.where(Store.status == status)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(Store.name.like(like), Store.city.like(like), Store.address.like(like))
        )
    stmt = stmt.order_by(Store.id).limit(limit).offset(offset)
    rows = list((await db.execute(stmt)).all())
    out = []
    for s, cnt in rows:
        data = StoreOut.model_validate(s).model_dump()
        data["stock_count"] = cnt or 0
        out.append(data)
    return out


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


# ---------------- 地理编码（v2.6）：地址 → GCJ-02 坐标 ----------------

GEOCODER_URL = "https://apis.map.qq.com/ws/geocoder/v1/"


def _tmap_geocode(address: str) -> dict:
    """同步调用腾讯位置服务「地址解析」WebService（在线程池里执行，避免阻塞事件循环）。"""
    qs = urllib.parse.urlencode(
        {"address": address, "key": settings.TMAP_SERVER_KEY, "output": "json"}
    )
    req = urllib.request.Request(
        GEOCODER_URL + "?" + qs, headers={"User-Agent": "FLY-CMS/1.0"}
    )
    with urllib.request.urlopen(req, timeout=settings.TMAP_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


@router.post("/geocode", response_model=StoreGeocodeOut)
async def geocode_address(
    payload: StoreGeocodeIn,
    _: CurrentMerchStoreOps = None,
):
    """地址 → 经纬度（GCJ-02）。服务端 Key 不返回给前端；未配置 Key 返回 501 由前端降级。"""
    # 先校验入参（客户端错误优先于「服务未配置」），保证前端拿到更准确的提示
    full = "".join(
        p for p in (payload.province, payload.city, payload.district, payload.address) if p
    ).strip()
    if not full:
        raise HTTPException(status_code=422, detail="请至少填写城市或详细地址")
    if not settings.TMAP_SERVER_KEY:
        raise HTTPException(
            status_code=501,
            detail="未配置服务端地图 Key（TMAP_SERVER_KEY），请手工点选或直接录入坐标",
        )

    try:
        raw = await asyncio.to_thread(_tmap_geocode, full)
    except Exception as exc:  # 网络/超时/解析失败统一成 502，不暴露 Key
        raise HTTPException(status_code=502, detail=f"地图服务请求失败：{exc}")

    if raw.get("status") != 0:
        raise HTTPException(
            status_code=502, detail=f"地址解析失败：{raw.get('message') or '未知错误'}"
        )
    res = raw.get("result") or {}
    loc = res.get("location") or {}
    if loc.get("lng") is None or loc.get("lat") is None:
        raise HTTPException(
            status_code=404, detail="未能解析出坐标，请补充更完整的地址或手工点选"
        )
    comp = res.get("address_components") or {}
    return StoreGeocodeOut(
        lng=float(loc["lng"]),
        lat=float(loc["lat"]),
        title=res.get("title"),
        address=res.get("address"),
        province=comp.get("province"),
        city=comp.get("city"),
        district=comp.get("district"),
        reliability=res.get("reliability"),
    ).model_dump()


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


# ---------------- 单店读写（必须放在 /geocode、/stock/* 之后） ----------------

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
    payload: StoreUpdate,
    current: CurrentMerchStoreOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """部分更新：只改本次显式提交的字段（v2.6 修复——此前用 StoreCreate 会全量覆盖）。"""
    store = await db.get(Store, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")
    data = payload.model_dump(exclude_unset=True)
    for k in _REQUIRED_NOT_NULL:
        if k in data and data[k] is None:
            raise HTTPException(status_code=422, detail=f"字段 {k} 不能为空")
    changed = {}
    for k, v in data.items():
        if getattr(store, k, None) != v:
            changed[k] = v
        setattr(store, k, v)
    await db.commit()
    await db.refresh(store)
    await log_operation(db, current, "update", "store", store.id, after=changed or None)
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
    # store_stocks 外键 ON DELETE CASCADE：删门店会连带清库存，审计里记一笔条数
    cnt = (
        await db.execute(
            select(func.count(StoreStock.id)).where(StoreStock.store_id == store_id)
        )
    ).scalar() or 0
    name = store.name
    await db.delete(store)
    await db.commit()
    await log_operation(
        db, current, "delete", "store", store_id,
        after={"name": name, "cascade_stock_rows": cnt},
    )
    await db.commit()
    return None
