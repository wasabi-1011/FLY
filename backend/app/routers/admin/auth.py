"""后台·鉴权：登录 / 当前用户（FR-B51 / FR-B54 / NFR-19）。"""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import CurrentAnyAdmin
from app.models.admin import AdminLoginLog, AdminUser
from app.schemas.admin import AdminUserOut, TokenOut
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/api/admin/auth", tags=["admin-auth"])

_TYPE = "bearer"


@router.post("/login", response_model=TokenOut)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    ip = request.client.host if request.client else None
    user = (
        await db.execute(
            select(AdminUser).where(AdminUser.username == form.username)
        )
    ).scalar_one_or_none()

    async def fail(reason: str, raise_):
        db.add(
            AdminLoginLog(
                user_id=user.id if user else None,
                username=form.username,
                success=False,
                fail_reason=reason,
                ip=ip,
            )
        )
        await db.commit()
        raise raise_

    if user is None or user.status.value != "active":
        await fail("用户不存在或已停用", HTTPException(401, "用户名或密码错误"))

    if user.locked_until and user.locked_until > datetime.utcnow():
        await fail("账号锁定中", HTTPException(403, "账号已锁定，请稍后再试"))

    if not verify_password(form.password, user.password_hash):
        user.failed_attempts += 1
        if user.failed_attempts >= settings.PASSWORD_MAX_FAIL:
            user.locked_until = datetime.utcnow() + timedelta(
                minutes=settings.LOCK_MINUTES
            )
        await fail("密码错误", HTTPException(401, "用户名或密码错误"))

    user.failed_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.utcnow()
    db.add(
        AdminLoginLog(
            user_id=user.id, username=user.username, success=True, ip=ip
        )
    )
    await db.commit()

    token = create_access_token(user.id, extra={"role": user.role.value})
    return TokenOut(
        access_token=token, role=user.role, username=user.username
    )


@router.get("/me", response_model=AdminUserOut)
async def me(current: CurrentAnyAdmin):
    return current
