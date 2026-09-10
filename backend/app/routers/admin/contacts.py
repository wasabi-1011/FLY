"""后台·留言管理（FR-B19 / NFR-22）。R2 权限；明文仅超管可见。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentContentOps
from app.enums import HandleStatus, Role
from app.models.contact import ContactMessage
from app.schemas.contact import ContactOut, ContactUpdate
from app.services.audit import log_operation

router = APIRouter(prefix="/api/admin/contacts", tags=["admin-contacts"])


def _mask(msg: ContactMessage) -> ContactOut:
    is_email = msg.contact_type.value == "email"
    c = msg.contact
    if is_email:
        local, _, domain = c.partition("@")
        masked = f"{local[:2]}{'*' * max(2, len(local) - 2)}@{domain}"
    else:
        masked = c[:3] + "*" * (len(c) - 5) + c[-2:] if len(c) >= 7 else c
    return ContactOut(
        id=msg.id, name=msg.name, company=msg.company,
        contact_type=msg.contact_type, contact_masked=masked,
        coop_type=msg.coop_type, content=msg.content,
        handle_status=msg.handle_status, remark=msg.remark,
        created_at=msg.created_at, show_full_contact=False,
    )


@router.get("", response_model=list[ContactOut])
async def list_contacts(
    handle_status: HandleStatus | None = Query(default=None),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentContentOps = None,
):
    stmt = select(ContactMessage)
    if handle_status is not None:
        stmt = stmt.where(ContactMessage.handle_status == handle_status)
    stmt = stmt.order_by(ContactMessage.created_at.desc())
    rows = list((await db.execute(stmt)).scalars().all())
    # 列表同样遵循脱敏规则；超管可见明文（FR-B19 / NFR-22）
    out = []
    for m in rows:
        item = _mask(m)
        if _.role == Role.SUPER_ADMIN:
            item.show_full_contact = True
            item.contact_full = m.contact
        out.append(item)
    return out


@router.get("/{contact_id}", response_model=ContactOut)
async def get_contact(
    contact_id: int,
    current: CurrentContentOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    msg = await db.get(ContactMessage, contact_id)
    if not msg:
        raise HTTPException(status_code=404, detail="留言不存在")
    out = _mask(msg)
    if current.role == Role.SUPER_ADMIN:
        out.show_full_contact = True
        out.contact_full = msg.contact
    return out


@router.patch("/{contact_id}", response_model=ContactOut)
async def update_contact(
    contact_id: int,
    payload: ContactUpdate,
    current: CurrentContentOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    msg = await db.get(ContactMessage, contact_id)
    if not msg:
        raise HTTPException(status_code=404, detail="留言不存在")
    if payload.handle_status is not None:
        msg.handle_status = payload.handle_status
    if payload.remark is not None:
        msg.remark = payload.remark
    if current.role == Role.SUPER_ADMIN:
        msg.handled_by = current.id
    await db.commit()
    await db.refresh(msg)
    out = _mask(msg)
    if current.role == Role.SUPER_ADMIN:
        out.show_full_contact = True
        out.contact_full = msg.contact
    await log_operation(db, current, "update", "contact", contact_id)
    await db.commit()
    return out
