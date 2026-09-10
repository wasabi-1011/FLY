"""内容域模型：Page / PageVersion / Block（CMS）/ Article（新闻）。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Enum as SAEnum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Boolean,
    DateTime,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import BlockType, NewsCategory, PageStatus, Status
from app.models.base import Base


class Page(Base):
    """CMS 页面（首页 / 专题页 / 固定页）。"""

    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    page_type: Mapped[str] = mapped_column(String(50), default="fixed")  # fixed|campaign
    status: Mapped[PageStatus] = mapped_column(
        SAEnum(PageStatus), default=PageStatus.DRAFT
    )
    current_version_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 并发编辑锁（FR-B03）：谁正在编辑该页
    locked_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    versions: Mapped[list["PageVersion"]] = relationship(
        back_populates="page",
        cascade="all, delete-orphan",
        order_by="PageVersion.version_no.desc()",
    )


class PageVersion(Base):
    """页面版本快照，保留 >=10 个支持回滚（FR-B06）。"""

    __tablename__ = "page_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    page_id: Mapped[int] = mapped_column(
        ForeignKey("pages.id", ondelete="CASCADE"), index=True
    )
    version_no: Mapped[int] = mapped_column(Integer)
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)

    page: Mapped["Page"] = relationship(back_populates="versions")
    blocks: Mapped[list["Block"]] = relationship(
        back_populates="version",
        cascade="all, delete-orphan",
        order_by="Block.sort",
    )


class Block(Base):
    """区块：11 种类型，config_json 存内容与样式（FR-B02 / FR-B04）。"""

    __tablename__ = "blocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    page_version_id: Mapped[int] = mapped_column(
        ForeignKey("page_versions.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[BlockType] = mapped_column(SAEnum(BlockType))
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)
    sort: Mapped[int] = mapped_column(Integer, default=0)
    mobile_visible: Mapped[bool] = mapped_column(Boolean, default=True)

    version: Mapped["PageVersion"] = relationship(back_populates="blocks")


class Article(Base):
    """新闻：分类固定企业新闻/行业资讯（FR-B12 / 10.2）。"""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    category: Mapped[NewsCategory] = mapped_column(
        SAEnum(NewsCategory), index=True
    )
    cover_image: Mapped[str | None] = mapped_column(String(512), nullable=True)
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # 出参经 XSS 过滤 NFR-18
    author: Mapped[str | None] = mapped_column(String(100), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        default=None, nullable=True, index=True
    )
    status: Mapped[Status] = mapped_column(
        SAEnum(Status), default=Status.DRAFT, index=True
    )
    seo_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    og_image: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )
