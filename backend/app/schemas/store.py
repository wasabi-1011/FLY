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
