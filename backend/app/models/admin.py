"""后台账号与权限模型：AdminUser / AdminLoginLog / OperationLog（10.2）。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Enum as SAEnum,
    Integer,
    String,
    Text,
    DateTime,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.enums import AdminStatus, Role
from app.models.base import Base


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(SAEnum(Role), default=Role.CONTENT_OPS)
    status: Mapped[AdminStatus] = mapped_column(
        SAEnum(AdminStatus), default=AdminStatus.ACTIVE
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class AdminLoginLog(Base):
    __tablename__ = "admin_login_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    username: Mapped[str] = mapped_column(String(100))
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    fail_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, index=True
    )


class OperationLog(Base):
    """操作日志（FR-B10 / FR-B55）。"""

    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    action_type: Mapped[str] = mapped_column(String(50))  # create/update/delete/publish
    target_type: Mapped[str] = mapped_column(String(50))
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    before: Mapped[str | None] = mapped_column(Text, nullable=True)
    after: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, index=True
    )
