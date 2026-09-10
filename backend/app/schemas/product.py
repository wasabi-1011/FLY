"""商品域 schema（系列 / 款式）。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.enums import Category, Season, Status


class CollectionBase(BaseModel):
    name: str
    subtitle: str | None = None
    category: Category
    year: int | None = None
    season: Season | None = None
    cover_image: str | None = None
    hero_image: str | None = None
    hero_video: str | None = None
    story: str | None = None
    sort_weight: int = 0
    status: Status = Status.DRAFT


class CollectionCreate(CollectionBase):
    slug: str


class CollectionUpdate(BaseModel):
    name: str | None = None
    subtitle: str | None = None
    category: Category | None = None
    year: int | None = None
    season: Season | None = None
    cover_image: str | None = None
    hero_image: str | None = None
    hero_video: str | None = None
    story: str | None = None
    sort_weight: int | None = None
    status: Status | None = None


class CollectionOut(CollectionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    published_at: datetime | None = None
    item_count: int = 0


class ItemBase(BaseModel):
    name: str
    collection_id: int
    item_code: str
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
    pass


class ItemUpdate(BaseModel):
    name: str | None = None
    collection_id: int | None = None
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


class ItemOut(ItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    category: Category  # 由系列继承，返回时带出
