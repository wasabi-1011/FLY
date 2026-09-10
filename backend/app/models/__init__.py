"""集中导出所有模型，供 init_db 与迁移注册。"""
from app.models.base import Base
from app.models.product import Collection, Item
from app.models.store import Store, StoreStock
from app.models.content import Page, PageVersion, Block, Article
from app.models.contact import ContactMessage
from app.models.admin import AdminUser, AdminLoginLog, OperationLog

__all__ = [
    "Base",
    "Collection",
    "Item",
    "Store",
    "StoreStock",
    "Page",
    "PageVersion",
    "Block",
    "Article",
    "ContactMessage",
    "AdminUser",
    "AdminLoginLog",
    "OperationLog",
]
