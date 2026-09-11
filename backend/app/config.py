"""运行时配置（pydantic-settings）。

数据库统一使用 SQLite（PRD v1.5 定稿）：sqlite+aiosqlite 单文件、零运维、开箱即跑。
如需未来扩展，ORM 已抽象方言，改 DATABASE_URL 即可切到 postgresql+asyncpg。
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    PROJECT_NAME: str = "FLY Brand Official Website API"
    API_V1_PREFIX: str = "/api"

    # 数据库：统一 SQLite（PRD v1.5 定稿，async + aiosqlite，单文件零运维）
    # 如需扩展可切 postgresql+asyncpg（ORM 已抽象方言，代码层无需改动）
    DATABASE_URL: str = "sqlite+aiosqlite:///./fly.db"
    DB_ECHO: bool = False

    # Redis：可选。未配置时缓存/限频降级为内存实现（仅单实例有效）
    REDIS_URL: str | None = None

    # 安全
    SECRET_KEY: str = "change-me-in-production-please-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8h，参考 FR-B54
    PASSWORD_MAX_FAIL: int = 5
    LOCK_MINUTES: int = 15

    # 留言限频（FR-F87 / FR-F76）
    CONTACT_LIMIT_PER_HOUR: int = 10

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    UPLOAD_MAX_MB: int = 10

    # 地图（腾讯位置服务）
    # 服务端 Key：仅用于后台「地址 → 坐标」地理编码，绝不返回给前端、不落库。
    # 未配置时地理编码接口返回 501，后台自动降级为人工点选/手工录入坐标。
    TMAP_SERVER_KEY: str | None = None
    # 地理编码超时（秒）
    TMAP_TIMEOUT: float = 5.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
