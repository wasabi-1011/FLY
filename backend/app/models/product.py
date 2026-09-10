"""商品域模型：系列 Collection / 款式 Item。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import Category, Season, Status
from app.models.base import Base


class Collection(Base):
    """系列：必须归属唯一品类（FR-B21 / 10.2）。"""

    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    subtitle: Mapped[str | None] = mapped_column(String(300), nullable=True)
    category: Mapped[Category] = mapped_column(SAEnum(Category), nullable=False, index=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    season: Mapped[Season | None] = mapped_column(SAEnum(Season), nullable=True)
    cover_image: Mapped[str | None] = mapped_column(String(512), nullable=True)
    hero_image: Mapped[str | None] = mapped_column(String(512), nullable=True)
    hero_video: Mapped[str | None] = mapped_column(String(512), nullable=True)
    story: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_weight: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[Status] = mapped_column(SAEnum(Status), default=Status.DRAFT, index=True)
    published_at: Mapped[datetime | None] = mapped_column(default=None, nullable=True)

    items: Mapped[list["Item"]] = relationship(
        back_populates="collection", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_collection_cat_status_pub", "category", "status", "published_at"),
    )


class Item(Base):
    """款式：归属唯一系列，品类由系列继承（FR-B22 / 10.2）。"""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    collection_id: Mapped[int] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"), index=True
    )
    is_hot: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    hot_sort: Mapped[int] = mapped_column(Integer, default=0)
    images: Mapped[list | None] = mapped_column(JSON, nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    fabric: Mapped[str | None] = mapped_column(String(300), nullable=True)
    colors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    fit_description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_weight: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[Status] = mapped_column(SAEnum(Status), default=Status.DRAFT, index=True)
    ext_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 二期扩展预留

    collection: Mapped["Collection"] = relationship(back_populates="items")

    __table_args__ = (Index("ix_item_hot", "is_hot", "hot_sort"),)
