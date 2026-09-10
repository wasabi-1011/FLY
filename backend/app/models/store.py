"""门店域模型：Store / StoreStock。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import Status, StoreType
from app.models.base import Base


class Store(Base):
    """门店：经纬度为 GCJ-02（FR-F45 / FR-B31）。"""

    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    province: Mapped[str] = mapped_column(String(50))
    city: Mapped[str] = mapped_column(String(50), index=True)
    district: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str] = mapped_column(String(512))
    lng: Mapped[float] = mapped_column(Float)  # GCJ-02
    lat: Mapped[float] = mapped_column(Float)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    business_hours: Mapped[str | None] = mapped_column(String(200), nullable=True)
    store_type: Mapped[StoreType] = mapped_column(
        SAEnum(StoreType), default=StoreType.STANDARD
    )
    images: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[Status] = mapped_column(
        SAEnum(Status), default=Status.ONLINE, index=True
    )

    stocks: Mapped[list["StoreStock"]] = relationship(
        back_populates="store", cascade="all, delete-orphan"
    )


class StoreStock(Base):
    """门店库存：仅后台内部查询，前台不展示数量（FR-B41~B47）。"""

    __tablename__ = "store_stocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="CASCADE"), index=True
    )
    item_code: Mapped[str] = mapped_column(String(64), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    store: Mapped["Store"] = relationship(back_populates="stocks")

    __table_args__ = (
        UniqueConstraint("store_id", "item_code", name="uq_store_item"),
    )
