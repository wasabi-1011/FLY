"""后台账号 / 鉴权 schema。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import AdminStatus, Role


class AdminUserCreate(BaseModel):
    username: str
    password: str
    role: Role = Role.CONTENT_OPS
    status: AdminStatus = AdminStatus.ACTIVE


class AdminUserUpdate(BaseModel):
    password: str | None = None
    role: Role | None = None
    status: AdminStatus | None = None


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    role: Role
    status: AdminStatus
    last_login_at: datetime | None = None
    created_at: datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role
    username: str


class OperationLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int | None = None
    username: str | None = None
    action_type: str
    target_type: str
    target_id: str | None = None
    before: str | None = None
    after: str | None = None
    created_at: datetime
