"""联系留言模型（FR-F86 / FR-B19 / 10.2）。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Enum as SAEnum,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.enums import ContactType, CoopType, HandleStatus
from app.models.base import Base


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contact_type: Mapped[ContactType] = mapped_column(SAEnum(ContactType))
    contact: Mapped[str] = mapped_column(String(200))
    coop_type: Mapped[CoopType | None] = mapped_column(
        SAEnum(CoopType), nullable=True
    )
    content: Mapped[str] = mapped_column(Text)
    handle_status: Mapped[HandleStatus] = mapped_column(
        SAEnum(HandleStatus), default=HandleStatus.PENDING, index=True
    )
    handled_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 软删除（留言管理·删除操作）：保留审计与个人信息删除权追溯，列表默认不展示
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, index=True
    )
