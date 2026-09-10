"""公开·联系留言提交（FR-F86 / FR-F87 / FR-F76）。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contact import ContactMessage
from app.schemas.contact import ContactCreate, ContactOut
from app.services.ratelimit import check_rate_limit

router = APIRouter(prefix="/api/contact", tags=["contact-public"])


@router.post("", response_model=ContactOut)
async def submit_contact(
    payload: ContactCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    client_ip = request.client.host if request.client else "unknown"
    allowed = await check_rate_limit(f"contact:{client_ip}")
    if not allowed:
        raise HTTPException(
            status_code=429, detail="提交过于频繁，请稍后再试"
        )

    # 验证码占位：生产接入验证码服务后在此校验 payload.captcha_token（FR-F87）
    msg = ContactMessage(
        name=payload.name,
        company=payload.company,
        contact_type=payload.contact_type,
        contact=payload.contact,
        coop_type=payload.coop_type,
        content=payload.content,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    masked = (
        payload.contact[:3] + "****"
        if payload.contact_type.value == "phone" and len(payload.contact) > 3
        else "****" + payload.contact[-2:]
    ) if payload.contact_type.value == "email" else (
        payload.contact[:3] + "****" + payload.contact[-2:]
        if len(payload.contact) >= 7
        else payload.contact
    )
    return ContactOut(
        id=msg.id,
        name=msg.name,
        company=msg.company,
        contact_type=msg.contact_type,
        contact_masked=masked,
        coop_type=msg.coop_type,
        content=msg.content,
        handle_status=msg.handle_status,
        remark=msg.remark,
        created_at=msg.created_at,
        show_full_contact=False,
    )
