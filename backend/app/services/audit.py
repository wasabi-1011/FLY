"""操作审计日志写入（FR-B10 / FR-B55）。"""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import AdminUser, OperationLog


def _dump(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, str):
        return v[:2000]
    try:
        return json.dumps(v, ensure_ascii=False, default=str)[:2000]
    except TypeError:
        return str(v)[:2000]


async def log_operation(
    db: AsyncSession,
    user: AdminUser | None,
    action_type: str,
    target_type: str,
    target_id: str | int | None = None,
    before: Any = None,
    after: Any = None,
) -> None:
    db.add(
        OperationLog(
            user_id=user.id if user else None,
            username=user.username if user else None,
            action_type=action_type,
            target_type=target_type,
            target_id=str(target_id) if target_id is not None else None,
            before=_dump(before),
            after=_dump(after),
        )
    )
