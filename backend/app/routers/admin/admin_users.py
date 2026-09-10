"""后台·账号与权限管理（FR-B51~B57）。仅超级管理员。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentSuperAdmin
from app.models.admin import AdminUser
from app.schemas.admin import AdminUserCreate, AdminUserOut, AdminUserUpdate
from app.security import hash_password
from app.services.audit import log_operation

router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


@router.get("", response_model=list[AdminUserOut])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentSuperAdmin = None,
):
    rows = list((await db.execute(select(AdminUser).order_by(AdminUser.id))).scalars().all())
    return [AdminUserOut.model_validate(u).model_dump(mode="json") for u in rows]


@router.post("", response_model=AdminUserOut, status_code=201)
async def create_user(
    payload: AdminUserCreate,
    current: CurrentSuperAdmin,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    if (
        await db.execute(
            select(AdminUser).where(AdminUser.username == payload.username)
        )
    ).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="用户名已存在")
    user = AdminUser(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
        status=payload.status,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    await log_operation(db, current, "create", "admin_user", user.id, after=payload.model_dump(exclude={"password"}))
    await db.commit()
    return AdminUserOut.model_validate(user).model_dump(mode="json")


@router.get("/{user_id}", response_model=AdminUserOut)
async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentSuperAdmin = None,
):
    user = await db.get(AdminUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")
    return AdminUserOut.model_validate(user).model_dump(mode="json")


@router.put("/{user_id}", response_model=AdminUserOut)
async def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    current: CurrentSuperAdmin,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    user = await db.get(AdminUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")
    data = payload.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        data["password_hash"] = hash_password(data.pop("password"))
    for k, v in data.items():
        setattr(user, k, v)
    await db.commit()
    await db.refresh(user)
    await log_operation(db, current, "update", "admin_user", user.id, after=payload.model_dump(exclude={"password"}, exclude_unset=True))
    await db.commit()
    return AdminUserOut.model_validate(user).model_dump(mode="json")
