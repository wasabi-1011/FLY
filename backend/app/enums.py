"""全站共享枚举（与 PRD 第 10 章数据模型一致）。"""
from __future__ import annotations

import enum


class Category(str, enum.Enum):
    """产品一级品类，固定枚举，不可后台增删（FR-B28 / FR-F28）。"""

    MEN = "men"
    WOMEN = "women"
    KIDS = "kids"


class Season(str, enum.Enum):
    SPRING_SUMMER = "SPRING_SUMMER"
    AUTUMN_WINTER = "AUTUMN_WINTER"
    CAPSULE = "CAPSULE"


class Status(str, enum.Enum):
    """通用上下线/草稿状态机（系列/款式/新闻/门店）。"""

    DRAFT = "draft"
    ONLINE = "online"
    OFFLINE = "offline"


class PageStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    OFFLINE = "offline"


class StoreType(str, enum.Enum):
    FLAGSHIP = "FLAGSHIP"
    STANDARD = "STANDARD"
    OUTLET = "OUTLET"


class ContactType(str, enum.Enum):
    PHONE = "phone"
    EMAIL = "email"


class CoopType(str, enum.Enum):
    HQ = "hq"            # 总部
    MEDIA = "media"      # 媒体
    CHANNEL = "channel"  # 渠道
    INVEST = "invest"    # 招商


class HandleStatus(str, enum.Enum):
    PENDING = "pending"
    CONTACTED = "contacted"
    CLOSED = "closed"


class Role(str, enum.Enum):
    """后台 RBAC 三种角色（3.2 节 R1/R2/R3）。"""

    SUPER_ADMIN = "SUPER_ADMIN"          # R1 超级管理员
    CONTENT_OPS = "CONTENT_OPS"          # R2 内容运营
    MERCH_STORE_OPS = "MERCH_STORE_OPS"  # R3 商品门店运营


class AdminStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class NewsCategory(str, enum.Enum):
    """新闻分类固定两项（FR-F54）。"""

    COMPANY = "company"
    INDUSTRY = "industry"


class BlockType(str, enum.Enum):
    """CMS 11 种区块类型（FR-B02）。"""

    FULLSCREEN_VISUAL = "FULLSCREEN_VISUAL"  # ① 全屏大视觉（首页轮播容器）
    IMAGE_BANNER = "IMAGE_BANNER"            # ② 图文 banner
    COLLECTION_RECOMMEND = "COLLECTION_RECOMMEND"  # ③ 系列推荐
    HOT_RECOMMEND = "HOT_RECOMMEND"          # ④ 热门推荐
    ITEM_RECOMMEND = "ITEM_RECOMMEND"        # ⑤ 款式推荐
    STORE_ENTRY = "STORE_ENTRY"              # ⑥ 门店入口
    NEWS_RECOMMEND = "NEWS_RECOMMEND"        # ⑦ 新闻推荐
    RICH_TEXT = "RICH_TEXT"                  # ⑧ 自定义富文本
    GALLERY = "GALLERY"                      # ⑨ 多图画廊
    VIDEO_EMBED = "VIDEO_EMBED"              # ⑩ 视频嵌入
    COLUMN_ENTRY = "COLUMN_ENTRY"            # ⑪ 栏目快捷入口
