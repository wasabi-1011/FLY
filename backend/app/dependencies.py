"""鉴权依赖：JWT 解析、当前用户、基于角色的访问控制（FR-B53 / NFR-19）。"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.enums import Role
from app.models.admin import AdminUser
from app.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/admin/auth/login", auto_error=True
)

_credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="无效或过期的凭证",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AdminUser:
    try:
        payload = decode_token(token)
        sub = payload.get("sub")
        if sub is None:
            raise _credentials_exc
        user_id = int(sub)
    except (JWTError, ValueError):
        raise _credentials_exc

    user = await db.get(AdminUser, user_id)
    if user is None or user.status.value != "active":
        raise _credentials_exc
    return user


def require_roles(*roles: Role):
    """生成依赖：当前用户角色必须在允许集合内，否则 403（越权防护 FR-B57）。"""

    async def checker(
        current: Annotated[AdminUser, Depends(get_current_user)],
    ) -> AdminUser:
        if current.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="权限不足"
            )
        return current

    return checker


# 常用角色约束
CurrentSuperAdmin = Annotated[
    AdminUser, Depends(require_roles(Role.SUPER_ADMIN))
]
CurrentContentOps = Annotated[
    AdminUser, Depends(require_roles(Role.SUPER_ADMIN, Role.CONTENT_OPS))
]
CurrentMerchStoreOps = Annotated[
    AdminUser, Depends(require_roles(Role.SUPER_ADMIN, Role.MERCH_STORE_OPS))
]
CurrentAnyAdmin = Annotated[AdminUser, Depends(get_current_user)]
