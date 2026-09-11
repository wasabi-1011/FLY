"""门店域 schema（Store / StoreStock）。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import Status, StoreType


class StoreBase(BaseModel):
    name: str
    province: str
    city: str
    district: str | None = None
    address: str
    lng: float  # GCJ-02
    lat: float
    phone: str | None = None
    business_hours: str | None = None
    store_type: StoreType = StoreType.STANDARD
    images: list | None = None
    status: Status = Status.ONLINE


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    name: str | None = None
    province: str | None = None
    city: str | None = None
    district: str | None = None
    address: str | None = None
    lng: float | None = None
    lat: float | None = None
    phone: str | None = None
    business_hours: str | None = None
    store_type: StoreType | None = None
    images: list | None = None
    status: Status | None = None


class StoreOut(StoreBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    # 后台列表专用：该门店关联的库存记录条数（公开接口不填充，恒为 None）。
    # 用途：删除前提示「会连带清除 N 条库存」，避免静默连删。
    stock_count: int | None = None


class StoreGeocodeIn(BaseModel):
    """后台「地址 → 坐标」请求（省/市/区 + 详细地址）。"""

    province: str | None = None
    city: str | None = None
    district: str | None = None
    address: str = ""


class StoreGeocodeOut(BaseModel):
    """地理编码结果：坐标一律 GCJ-02，与腾讯底图、Store.lng/lat 三者一致。"""

    lng: float
    lat: float
    title: str | None = None
    address: str | None = None
    province: str | None = None
    city: str | None = None
    district: str | None = None
    reliability: int | None = None  # 可信度，<=7 建议人工复核


class StoreStockCreate(BaseModel):
    store_id: int
    item_code: str
    quantity: int = 0


class StoreStockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    store_id: int
    item_code: str
    quantity: int
    updated_at: datetime


class StoreAvailability(BaseModel):
    """前台「附近有售」仅返回城市名，不返回数量（FR-F28 / FR-B41）。"""

    item_code: str
    cities: list[str]
