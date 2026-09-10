"""联系留言 schema。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import ContactType, CoopType, HandleStatus


class ContactCreate(BaseModel):
    name: str
    company: str | None = None
    contact_type: ContactType
    contact: str
    coop_type: CoopType | None = None
    content: str
    # 验证码占位：生产接入验证码服务后在此校验（FR-F87）
    captcha_token: str | None = None


class ContactUpdate(BaseModel):
    handle_status: HandleStatus | None = None
    remark: str | None = None


class ContactOut(BaseModel):
    """后台列表/详情；phone/email 默认脱敏（FR-B19 / NFR-22）。"""

    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    company: str | None = None
    contact_type: ContactType
    contact_masked: str
    coop_type: CoopType | None = None
    content: str
    handle_status: HandleStatus
    remark: str | None = None
    created_at: datetime
    show_full_contact: bool = False  # 仅超管为 True
    contact_full: str | None = None  # 仅超管返回明文
