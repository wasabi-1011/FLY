"""异步数据库引擎与会话；统一 SQLite(async aiosqlite)，预留 PostgreSQL(asyncpg) 迁移能力。"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL, echo=settings.DB_ECHO, future=True
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """建表（开发期用；生产请用 Alembic 迁移）。"""
    from app import models  # noqa: F401 注册所有模型

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# 延迟导入避免循环
from app.models.base import Base  # noqa: E402
