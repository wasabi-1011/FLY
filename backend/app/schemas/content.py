"""内容域 schema（CMS Page/Block / Article）。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.enums import BlockType, NewsCategory, PageStatus, Status


# ---------- CMS 区块 / 页面 ----------

class BlockBase(BaseModel):
    type: BlockType
    config_json: dict = {}
    sort: int = 0
    mobile_visible: bool = True


class BlockOut(BlockBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    page_version_id: int


class PageBase(BaseModel):
    slug: str
    title: str
    page_type: str = "fixed"


class PageCreate(PageBase):
    blocks: list[BlockBase] = []  # 创建即生成首个版本草稿


class PageUpdate(BaseModel):
    title: str | None = None
    status: PageStatus | None = None
    blocks: list[BlockBase] | None = None  # 提交新区块即生成新版本草稿


class PageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    title: str
    page_type: str
    status: PageStatus
    current_version_id: int | None = None
    updated_at: datetime | None = None


class PageVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    version_no: int
    created_by: int | None = None
    created_at: datetime
    note: str | None = None
    blocks: list[BlockOut] = []


class PublishedPageOut(BaseModel):
    """前台读取的已发布页面（含当前版本区块）。"""

    slug: str
    title: str
    page_type: str
    blocks: list[BlockOut] = []


# ---------- 新闻 ----------

class ArticleBase(BaseModel):
    title: str
    category: NewsCategory
    cover_image: str | None = None
    summary: str | None = None
    content: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    status: Status = Status.DRAFT
    seo_title: str | None = None
    seo_description: str | None = None
    og_image: str | None = None


class ArticleCreate(ArticleBase):
    slug: str


class ArticleUpdate(BaseModel):
    title: str | None = None
    category: NewsCategory | None = None
    cover_image: str | None = None
    summary: str | None = None
    content: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    status: Status | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    og_image: str | None = None


class ArticleOut(ArticleBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
