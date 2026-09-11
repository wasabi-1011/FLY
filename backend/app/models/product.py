"""商品域模型：款式 Item（主体）/ 系列 Collection（挂在款式下，选填）。

层级（v2.2 起）：
    品类（men / women / kids，固定枚举）
       └─ 款式 Item（必有品类）
             └─ 系列 Collection（选填，0..n）

与旧版的区别：
    - 旧版：系列在上（系列有自己的品类），款式挂系列 —— 已废弃。
    - 新版：款式是主体，自带品类；系列降为款式下的可选分组，用 item_id 关联。
"""
from __future__ import annotations

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


class Item(Base):
    """款式：服装主体，必归属唯一品类；系列为可选项。"""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[Category] = mapped_column(SAEnum(Category), nullable=False, index=True)
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

    collections: Mapped[list["Collection"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="Collection.id",
    )

    __table_args__ = (
        Index("ix_item_cat_status", "category", "status"),
        Index("ix_item_hot", "is_hot", "hot_sort"),
    )


class Collection(Base):
    """系列：挂在某个款式下的可选分组（0..n）；品类由所属款式继承，不再单独存储。"""

    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    season: Mapped[Season | None] = mapped_column(SAEnum(Season), nullable=True)
    cover_image: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[Status] = mapped_column(SAEnum(Status), default=Status.ONLINE, index=True)

    item: Mapped["Item"] = relationship(back_populates="collections")
