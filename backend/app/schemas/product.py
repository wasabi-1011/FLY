"""商品域 schema（款式 Item 主体 / 系列 Collection 挂在款式下）。"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from app.enums import Category, Season, Status


class ItemBase(BaseModel):
    name: str
    category: Category
    is_hot: bool = False
    hot_sort: int = 0
    images: Any = None
    video_url: str | None = None
    fabric: str | None = None
    colors: Any = None
    fit_description: str | None = None
    description: str | None = None
    sort_weight: int = 0
    status: Status = Status.DRAFT
    ext_json: dict | None = None


class ItemCreate(ItemBase):
    # v2.3：款号可留空，留空由后端按「品类前缀 + 序号」自动生成（CO-SW001 / CO-MN002 / CO-KD005）。
    item_code: str | None = None


class ItemUpdate(BaseModel):
    name: str | None = None
    category: Category | None = None
    is_hot: bool | None = None
    hot_sort: int | None = None
    images: Any = None
    video_url: str | None = None
    fabric: str | None = None
    colors: Any = None
    fit_description: str | None = None
    description: str | None = None
    sort_weight: int | None = None
    status: Status | None = None
    ext_json: dict | None = None


class CollectionBase(BaseModel):
    name: str
    year: int | None = None
    season: Season | None = None
    cover_image: str | None = None
    status: Status = Status.ONLINE


class CollectionCreate(CollectionBase):
    item_id: int


class CollectionUpdate(BaseModel):
    name: str | None = None
    year: int | None = None
    season: Season | None = None
    cover_image: str | None = None
    status: Status | None = None


class CollectionOut(CollectionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    item_id: int
    # 便于后台列表展示所属款式（非必填，按需填充）
    item_code: str | None = None
    item_name: str | None = None


class ItemOut(ItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    item_code: str
    series: list[CollectionOut] = []
