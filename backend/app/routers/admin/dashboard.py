"""后台·仪表盘统计与操作日志（FR-B10 / FR-B55）。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentAnyAdmin
from app.models.admin import AdminUser, OperationLog
from app.models.contact import ContactMessage
from app.models.content import Article, Page
from app.models.product import Collection, Item
from app.models.store import Store
from app.schemas.admin import OperationLogOut

router = APIRouter(prefix="/api/admin", tags=["admin-dashboard"])


@router.get("/dashboard/stats")
async def stats(
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentAnyAdmin = None,
):
    async def _count(model, *where):
        stmt = select(func.count()).select_from(model)
        for w in where:
            stmt = stmt.where(w)
        return (await db.execute(stmt)).scalar() or 0

    return {
        "collections": await _count(Collection),
        "items": await _count(Item),
        "stores": await _count(Store, Store.status == "online"),
        "news": await _count(Article, Article.status == "online"),
        "published_pages": await _count(Page, Page.status == "published"),
        "contacts_pending": await _count(
            ContactMessage, ContactMessage.handle_status == "pending"
        ),
        "admin_users": await _count(AdminUser),
    }


@router.get("/operation-logs", response_model=list[OperationLogOut])
async def operation_logs(
    action_type: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentAnyAdmin = None,
):
    stmt = select(OperationLog)
    if action_type:
        stmt = stmt.where(OperationLog.action_type == action_type)
    if user_id is not None:
        stmt = stmt.where(OperationLog.user_id == user_id)
    stmt = stmt.order_by(OperationLog.created_at.desc()).limit(limit)
    rows = list((await db.execute(stmt)).scalars().all())
    return [OperationLogOut.model_validate(r).model_dump(mode="json") for r in rows]
