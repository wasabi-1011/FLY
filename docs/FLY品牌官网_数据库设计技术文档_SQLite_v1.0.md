# FLY 品牌官网 · 数据库设计技术文档（SQLite）

> 文档版本：v1.1 ｜ 创建日期：2026-09-09（v1.1 同日更新）｜ 状态：技术评审版
> 依据：`docs/FLY品牌官网_PRD_v1.0.md`（v1.6 评审修订版）第 9/10 章 + 后端现有 `backend/app/models/**` 实现
> 配套文件：`docs/FLY官网_SQLite建表DDL.sql`（SQLAlchemy 生成的最终可执行 DDL）
> **v1.1 变更**：`items` 表新增 `price` 价格**记录字段**（NUMERIC(10,2)，可空），用途为品牌方主数据记录（吊牌/参考零售价）；**后端本期不读写、前台不展示**，Non-goals N5 不受影响。建表 DDL 已同步补列，但 ORM 模型暂未映射（按"后端不使用"要求），详见 §4.2 说明。

---

## 0. 一页结论

本项目数据库确定为 **SQLite（异步，单文件）**，与后端 FastAPI + SQLAlchemy 2.0（async）配套，**开箱即跑、零部署**。对应 PRD v1.5 变更：删除"PostgreSQL（主）+ Redis"表述，统一为 SQLite。

全站共有 **12 张业务表、6 组领域枚举**，无其他存储对象（素材文件落磁盘不落库，见 §3.6）。核心关系：

```
Category(枚举: men/women/kids)  → 1:N → Collection(系列) → 1:N → Item(款式) → N:1 ← StoreStock(门店库存)
Store(门店)                     → 1:N → StoreStock
Page(CMS页面) → 1:N → PageVersion(版本) → 1:N → Block(区块)
Article(新闻) ｜ ContactMessage(留言)
AdminUser(后台账号·角色为枚举) ｜ AdminLoginLog / OperationLog(日志)
```

业务定位约束（来自 PRD Non-goals）：**无交易、无会员、无 SKU、无价格/尺码前台展示**；商品以「品类 → 系列 → 款式」两级粒度组织，`is_hot` 为人工打标；库存为后台内部工具、前台不展示数量。

---

## 1. 设计目标与原则

| # | 原则 | 落地 |
|---|---|---|
| 1 | **与 PRD 数据模型严格对齐** | 12 张表均能在 PRD 第 10 章找到出处；字段语义一致 |
| 2 | **与后端代码一致**（唯一例外见 §4.2） | 本文档表结构以 `backend/app/models/**` 实际映射为准（SQLAlchemy 2.0，已用其方言导出 DDL 校验）；**唯一例外：`items.price`**——v1.1 品牌方要求的记录字段，ORM 未映射（后端不读写），见 §4.2 |
| 3 | **数据库确定为 SQLite** | async 驱动 `aiosqlite`，单文件 `fly.db`；配置见 `backend/app/config.py`（`DATABASE_URL`） |
| 4 | 枚举值可追溯 | 全部枚举在 `backend/app/enums.py` 定义，本文档逐项列出取值 |
| 5 | JSON 扩展位 | 款式价格已独立为 `items.price` 记录字段（v1.1，后端不读写）；`ext_json` 预留二期 SKU/尺码 等，本期前台不消费 |

> **兼容性说明**：虽然生产可选 PostgreSQL（ORM 已抽象方言），但**本项目决策以 SQLite 为唯一数据库**，不再引入 PostgreSQL/Redis 作为默认依赖。

---

## 2. 命名与类型规范

### 2.1 表名/字段名

- 表名：蛇形复数（`collections`、`store_stocks`、`contact_messages`…）
- 字段：蛇形单数（`item_code`、`sort_weight`…）
- 主键统一 `id INTEGER PRIMARY KEY`；布尔字段命名 `is_*`/`mobile_visible`/`success`
- 索引命名：`ix_<表>_<列>`；唯一索引沿用该规则（SQLAlchemy 对 `unique=True` 生成的索引名）；联合唯一约束自定义 `uq_<表>_<列>`（如 `uq_store_item`）

### 2.2 SQLAlchemy 类型 → SQLite 实际类型映射

| Python/SQLAlchemy | SQLite 建表类型 | 说明 |
|---|---|---|
| `int` / `Integer` / PK | `INTEGER` | 自增主键 `INTEGER PRIMARY KEY`（rowid 别名） |
| `bool` / `Boolean` | `BOOLEAN`（存 0/1） | SQLite 无原生布尔，以 0/1 存储 |
| `str` / `String(n)` | `VARCHAR(n)` | 长度限制由应用层/建表声明约束 |
| `Text` | `TEXT` | 富文本/长文 |
| `float` / `Float` | `FLOAT`（存 REAL） | 经纬度等 |
| `Decimal` / `Numeric(10,2)` | `NUMERIC(10,2)`（NUMERIC 亲和性） | 金额类：`items.price` 吊牌/参考零售价（元），两位小数 |
| `datetime` / `DateTime` | `DATETIME`（存 TEXT，ISO 格式） | `default=datetime.utcnow`；统一 UTC 存储 |
| `JSON` | `JSON`（SQLAlchemy 序列化为 TEXT） | 数组/字典结构，见 §3.5 |
| `Enum(...)`（`SAEnum`） | `VARCHAR(n)` | 存储枚举字符串值，见 §3.4 |

---

## 3. 全站存储对象清单

### 3.1 存储对象总览（12 张表）

| # | 表名 | 中文名 | 所属领域 | PRD 出处 | 说明 |
|---|---|---|---|---|---|
| 1 | `collections` | 系列 | 商品域 | 10.2 Collection | 系列归属唯一品类 |
| 2 | `items` | 款式 | 商品域 | 10.2 Item | 款式归属唯一系列 |
| 3 | `stores` | 门店 | 门店域 | 10.2 Store | 含 GCJ-02 坐标 |
| 4 | `store_stocks` | 门店库存 | 门店域 | 10.2 StoreStock | 内部工具，前台不展示数量 |
| 5 | `articles` | 新闻 | 内容域 | 10.2 Article | 企业新闻/行业资讯 |
| 6 | `pages` | CMS 页面 | 内容域 | 10.2 Page | 首页/专题页/固定页 |
| 7 | `page_versions` | 页面版本 | 内容域 | 10.2 PageVersion | 版本快照 ≥10 可回滚 |
| 8 | `blocks` | CMS 区块 | 内容域 | 10.2 Block | 11 种区块类型 |
| 9 | `contact_messages` | 联系留言 | 内容域 | 10.2 ContactMessage | 「联系我们」表单 |
| 10 | `admin_users` | 后台账号 | 账号域 | 10.2 AdminUser | 角色为枚举（R1/R2/R3） |
| 11 | `admin_login_logs` | 登录日志 | 账号域 | 10.2 AdminLoginLog | 登录成功/失败/锁定 |
| 12 | `operation_logs` | 操作日志 | 账号域 | 10.2 OperationLog | 关键操作留痕 |

### 3.2 非表存储对象

| 对象 | 存储方式 | 说明 |
|---|---|---|
| 品类 Category | **枚举值，不建表** | `men/women/kids`，固定不可增删（FR-B28） |
| 角色 Role | **枚举值，不建表** | 轻量 RBAC 三角色（SUPER_ADMIN/CONTENT_OPS/MERCH_STORE_OPS） |
| 素材文件（图片/视频） | **磁盘 `uploads/` 目录 + URL 引用** | 数据库仅存 URL 字符串；一期本地磁盘，二期切 OSS/COS |
| 富文本中的图片 | 同上 | 经上传接口落盘后以 URL 写入正文 |
| 首页轮播帧图片 | 同上 | 作为 URL 存在 `Block.config_json` |

> 素材不建库表是刻意决策：一期素材量小、URL 引用足够；FR-B16「素材库」仅指后台可视化选择文件能力，不要求数据库元数据表（如需引用统计/删除保护可在二期加 `media_assets` 表，本文档预留说明见 §6.3）。

### 3.3 关系与级联策略

| 关系 | 外键 | 级联 | 删除语义 |
|---|---|---|---|
| Collection 1:N Item | `items.collection_id → collections.id` | `ON DELETE CASCADE` | 删除系列级联删款式 |
| Store 1:N StoreStock | `store_stocks.store_id → stores.id` | `ON DELETE CASCADE` | 删除门店级联删其库存 |
| Item 1:N StoreStock（逻辑关联） | `store_stocks.item_code` ↔ `items.item_code` | 无物理外键 | 见下方说明 |
| Page 1:N PageVersion | `page_versions.page_id → pages.id` | `ON DELETE CASCADE` | 删除页面级联删版本 |
| PageVersion 1:N Block | `blocks.page_version_id → page_versions.id` | `ON DELETE CASCADE` | 删除版本级联删区块 |
| ContactMessage N:1 AdminUser（逻辑） | `contact_messages.handled_by` → `admin_users.id` | 无物理外键 | 处理人逻辑引用 |
| Page N:1 AdminUser（逻辑） | `pages.locked_by` / `page_versions.created_by` → `admin_users.id` | 无物理外键 | 编辑锁/创建人逻辑引用 |

> **说明**：`store_stocks.item_code` 采用"业务主键引用"而非外键——PRD 明确款号 `item_code` 是库存关联主键且唯一（`items.item_code` UNIQUE）。出于"款式删除不应被历史库存记录阻塞"及 SQLite 外键对非主键唯一列引用限制的考量，代码层未建物理 FK，由**应用层保证存在性**（库存导入时校验款号存在）。这是**有意设计**，非遗漏。
>
> ⚠️ **SQLite 外键默认关闭**：需在连接时执行 `PRAGMA foreign_keys=ON`（SQLAlchemy async 下建议用 `event.listens_for(engine.sync_engine, "connect")` 注入）。项目 `app/database.py` 当前未显式设置，若需物理级联生效应在启动时补上（见 §6.2 待确认项）。

### 3.4 枚举字典（全部值）

> 枚举在 SQLite 中以字符串存储（`VARCHAR(n)`），括号内为 DDL 长度依据。

| 枚举 | 存储长度 | 取值 | 归属字段 |
|---|---|---|---|
| `Category` 品类 | VARCHAR(5) | `men` / `women` / `kids` | `collections.category` |
| `Season` 季节 | VARCHAR(13) | `SPRING_SUMMER` / `AUTUMN_WINTER` / `CAPSULE` | `collections.season` |
| `Status` 通用状态 | VARCHAR(7) | `draft` / `online` / `offline` | `collections/items/stores/articles.status` |
| `PageStatus` 页面状态 | VARCHAR(9) | `draft` / `published` / `offline` | `pages.status` |
| `StoreType` 门店类型 | VARCHAR(8) | `FLAGSHIP` / `STANDARD` / `OUTLET` | `stores.store_type` |
| `NewsCategory` 新闻分类 | VARCHAR(8) | `company` / `industry` | `articles.category` |
| `ContactType` 联系类型 | VARCHAR(5) | `phone` / `email` | `contact_messages.contact_type` |
| `CoopType` 合作类型 | VARCHAR(7) | `hq` / `media` / `channel` / `invest` | `contact_messages.coop_type` |
| `HandleStatus` 处理状态 | VARCHAR(9) | `pending` / `contacted` / `closed` | `contact_messages.handle_status` |
| `Role` 后台角色 | VARCHAR(15) | `SUPER_ADMIN` / `CONTENT_OPS` / `MERCH_STORE_OPS` | `admin_users.role` |
| `AdminStatus` 账号状态 | VARCHAR(8) | `active` / `disabled` | `admin_users.status` |
| `BlockType` 区块类型 | VARCHAR(20) | 见 §3.5 区块类型表（11 种） | `blocks.type` |

### 3.5 JSON 字段约定

| 表 | 字段 | 结构 | 示例 |
|---|---|---|---|
| `items` | `images` | 字符串数组（主图 URL，≥1 张） | `["/uploads/i1.jpg","/uploads/i2.jpg"]` |
| `items` | `colors` | 对象数组 `[{name,hex}]` | `[{"name":"曜石黑","hex":"#1A1A1A"}]` |
| `items` | `ext_json` | 二期扩展预留（SKU/尺码 等；价格已独立为 `price` 列，v1.1），本期 `null` | `null` |
| `stores` | `images` | 字符串数组（门店照片 URL） | `["/uploads/s1.jpg"]` |
| `blocks` | `config_json` | 区块内容与样式配置（结构随 `type` 而异） | 见下 |

**`Block.config_json` 的 11 种区块类型（`BlockType` 枚举）与结构**：

| type | 含义 | config_json 关键内容 |
|---|---|---|
| `FULLSCREEN_VISUAL` | ① 全屏大视觉（首页轮播容器） | `frames: [{image/video, 叠加文字三层, visible, sort}]`（≥3 帧） |
| `IMAGE_BANNER` | ② 图文 banner | `image、title、link、bg_color` |
| `COLLECTION_RECOMMEND` | ③ 系列推荐 | `collection_ids[]` 或按条件引用 |
| `HOT_RECOMMEND` | ④ 热门推荐 | `category 筛选、limit`（8 款） |
| `ITEM_RECOMMEND` | ⑤ 款式推荐 | `item_ids[]` |
| `STORE_ENTRY` | ⑥ 门店入口 | `标题、城市预设、地图缩略开关` |
| `NEWS_RECOMMEND` | ⑦ 新闻推荐 | `category 筛选、limit` |
| `RICH_TEXT` | ⑧ 自定义富文本 | `html`（经 XSS 白名单） |
| `GALLERY` | ⑨ 多图画廊 | `images[]` |
| `VIDEO_EMBED` | ⑩ 视频嵌入 | `video_url、封面` |
| `COLUMN_ENTRY` | ⑪ 栏目快捷入口 | 五大栏目宫格配置 |

> `config_json` 详细字段随前端渲染约定迭代，后端只负责 JSON 存储与透传；结构校验在 schema 层做宽松约束。本文档不锁定死结构（保持 CMS 灵活性）。

---

## 4. 逐表字段定义（12 张表）

> 每张表给出：用途 → 字段表（名称 / SQLite 类型 / 空 / 默认 / 说明）→ 索引与约束。
> ⚠️ 表内字段以 `backend/app/models/**` 为准；DDL 以 `docs/FLY官网_SQLite建表DDL.sql` 为准。

### 4.1 `collections` 系列

**用途**：商品系列，归属唯一品类；URL 路径含 `slug`（发布后不可改）。

| 字段 | 类型 | 空 | 默认 | 说明 |
|---|---|---|---|---|
| `id` | INTEGER PK | 否 | 自增 | |
| `name` | VARCHAR(200) | 否 | | 系列名 |
| `slug` | VARCHAR(200) | 否 | | **UNIQUE**，URL 段，小写字母/数字/连字符 |
| `subtitle` | VARCHAR(300) | 是 | | 副标题 |
| `category` | VARCHAR(5) | 否 | | 枚举 men/women/kids（必填） |
| `year` | INTEGER | 是 | | 年份 |
| `season` | VARCHAR(13) | 是 | | 枚举季节 |
| `cover_image` | VARCHAR(512) | 是 | | 列表封面 URL |
| `hero_image` | VARCHAR(512) | 是 | | 详情页大视觉 URL |
| `hero_video` | VARCHAR(512) | 是 | | 详情页视频 URL |
| `story` | TEXT | 是 | | 系列故事富文本 |
| `sort_weight` | INTEGER | 否 | 0 | 排序权重，越大越靠前 |
| `status` | VARCHAR(7) | 否 | draft | 枚举 draft/online/offline |
| `published_at` | DATETIME | 是 | | 发布时间 |

**索引**：`ix_collections_slug`(UNIQUE)、`ix_collections_category`、`ix_collections_status`、`ix_collection_cat_status_pub(category,status,published_at)`（支撑品类页列表）。

### 4.2 `items` 款式

**用途**：商品款式，归属唯一系列；`item_code` 款号为库存关联业务主键。v1.1 起含 `price` 价格**记录字段**（仅主数据记录用途，后端本期不读写、前台不展示）；无尺码/SKU/库存字段（Non-goals N5），其余二期扩展走 `ext_json`。

| 字段 | 类型 | 空 | 默认 | 说明 |
|---|---|---|---|---|
| `id` | INTEGER PK | 否 | 自增 | |
| `item_code` | VARCHAR(64) | 否 | | **UNIQUE**，款号，库存关联主键 |
| `name` | VARCHAR(200) | 否 | | 款名 |
| `collection_id` | INTEGER FK | 否 | | → `collections.id`，ON DELETE CASCADE |
| `is_hot` | BOOLEAN | 否 | false | 人工打标热门，禁止自动计算 |
| `hot_sort` | INTEGER | 否 | 0 | 热门排序，is_hot=true 时生效 |
| `images` | JSON | 是 | | 主图数组（≥1） |
| `video_url` | VARCHAR(512) | 是 | | 可选视频 |
| `fabric` | VARCHAR(300) | 是 | | 面料成分 |
| `colors` | JSON | 是 | | `[{name,hex}]` |
| `price` | NUMERIC(10,2) | 是 | | **v1.1 新增·记录字段**：吊牌/参考零售价（元），两位小数。后端本期不读写、前台不展示（N5 不变） |
| `fit_description` | VARCHAR(300) | 是 | | 版型描述 |
| `description` | TEXT | 是 | | 设计说明富文本 |
| `sort_weight` | INTEGER | 否 | 0 | 排序权重 |
| `status` | VARCHAR(7) | 否 | draft | 枚举 |
| `ext_json` | JSON | 是 | | 二期扩展预留（SKU/尺码 等；价格已独立为 `price` 列，v1.1） |

**索引**：`ix_items_item_code`(UNIQUE)、`ix_items_collection_id`、`ix_items_status`、`ix_items_is_hot`、`ix_item_hot(is_hot,hot_sort)`（支撑热门推荐页）。

> **关于 `price`（v1.1 落地方式）**：品牌方要求款式主数据包含价格，但**后端本期不使用**。因此——① 建表 DDL（`docs/FLY官网_SQLite建表DDL.sql`）已补 `price NUMERIC(10,2)` 列（脚本内有注释）；② ORM 模型 `backend/app/models/product.py` 暂**不映射**该列，SQLAlchemy `create_all` 建出的库不含此列（现有 `fly.db` 亦无，如需启用需模型补列 + 迁移/重建）；③ 前后台接口均不返回价格字段，前台不展示（Non-goals N5 不变）。

### 4.3 `stores` 门店

**用途**：门店主数据，含 GCJ-02 经纬度（地图选点获取，禁止手填）。

| 字段 | 类型 | 空 | 默认 | 说明 |
|---|---|---|---|---|
| `id` | INTEGER PK | 否 | 自增 | |
| `name` | VARCHAR(200) | 否 | | 门店名 |
| `province` | VARCHAR(50) | 否 | | 省 |
| `city` | VARCHAR(50) | 否 | | 市（城市筛选/地图聚类） |
| `district` | VARCHAR(50) | 是 | | 区/商圈 |
| `address` | VARCHAR(512) | 否 | | 详细地址 |
| `lng` | FLOAT | 否 | | 经度（GCJ-02） |
| `lat` | FLOAT | 否 | | 纬度（GCJ-02） |
| `phone` | VARCHAR(50) | 是 | | 联系电话 |
| `business_hours` | VARCHAR(200) | 是 | | 营业时间 |
| `store_type` | VARCHAR(8) | 否 | STANDARD | 枚举 FLAGSHIP/STANDARD/OUTLET |
| `images` | JSON | 是 | | 门店照片 URL 数组 |
| `status` | VARCHAR(7) | 否 | online | 枚举（默认上线） |

**索引**：`ix_stores_city`、`ix_stores_status`。补充查询建议：城市筛选与地图点位查询走 city+status。

### 4.4 `store_stocks` 门店库存

**用途**：后台内部有货查询（FR-B41~B47）；前台不展示数量。唯一键 = 门店 + 款号，重复导入为更新。

| 字段 | 类型 | 空 | 默认 | 说明 |
|---|---|---|---|---|
| `id` | INTEGER PK | 否 | 自增 | |
| `store_id` | INTEGER FK | 否 | | → `stores.id`，ON DELETE CASCADE |
| `item_code` | VARCHAR(64) | 否 | | 款号（逻辑引用 `items.item_code`） |
| `quantity` | INTEGER | 否 | 0 | 可售数量 |
| `updated_at` | DATETIME | 否 | utcnow | 数据更新时间（时效标记 FR-B46） |

**约束/索引**：`CONSTRAINT uq_store_item UNIQUE(store_id, item_code)`；`ix_store_stocks_store_id`、`ix_store_stocks_item_code`。

### 4.5 `articles` 新闻

**用途**：企业新闻/行业资讯，含 SEO 元数据与定时发布。

| 字段 | 类型 | 空 | 默认 | 说明 |
|---|---|---|---|---|
| `id` | INTEGER PK | 否 | 自增 | |
| `title` | VARCHAR(300) | 否 | | 标题 |
| `slug` | VARCHAR(255) | 否 | | **UNIQUE**，URL 段 |
| `category` | VARCHAR(8) | 否 | | 枚举 company/industry（固定两项） |
| `cover_image` | VARCHAR(512) | 是 | | 封面图 URL |
| `summary` | VARCHAR(500) | 是 | | 摘要 |
| `content` | TEXT | 是 | | 正文富文本（出参 XSS 过滤） |
| `author` | VARCHAR(100) | 是 | | 作者/来源 |
| `published_at` | DATETIME | 是 | | 发布时间（支持定时发布） |
| `status` | VARCHAR(7) | 否 | draft | 枚举 |
| `seo_title` | VARCHAR(200) | 是 | | SEO title |
| `seo_description` | VARCHAR(300) | 是 | | SEO description |
| `og_image` | VARCHAR(512) | 是 | | OG 分享图 |
| `created_at` | DATETIME | 否 | utcnow | |
| `updated_at` | DATETIME | 否 | utcnow | onupdate 自动刷新 |

**索引**：`ix_articles_slug`(UNIQUE)、`ix_articles_category`、`ix_articles_status`、`ix_articles_published_at`（支撑分类列表与排序）。

### 4.6 `pages` CMS 页面

**用途**：CMS 页面容器——固定页（首页/关于我们 4 页/招聘 2 页）+ 专题页（campaign）。

| 字段 | 类型 | 空 | 默认 | 说明 |
|---|---|---|---|---|
| `id` | INTEGER PK | 否 | 自增 | |
| `slug` | VARCHAR(255) | 否 | | **UNIQUE**，如 `home`、`campaign/2026aw` |
| `title` | VARCHAR(200) | 否 | | 页面名 |
| `page_type` | VARCHAR(50) | 否 | fixed | `fixed`（固定页） / `campaign`（专题页） |
| `status` | VARCHAR(9) | 否 | draft | 枚举 draft/published/offline |
| `current_version_id` | INTEGER | 是 | | 当前生效版本 id（逻辑引用 page_versions） |
| `locked_by` | INTEGER | 是 | | 并发编辑锁：占用编辑的管理员 id |
| `locked_at` | DATETIME | 是 | | 锁时间 |
| `created_at` | DATETIME | 否 | utcnow | |
| `updated_at` | DATETIME | 否 | utcnow | |

**索引**：`ix_pages_slug`(UNIQUE)。（固定页六个：about/fly、about/brand、about/history、about/contact、join/social、join/campus + home）

### 4.7 `page_versions` 页面版本

**用途**：页面版本快照，保留 ≥10 个，支持一键回滚（FR-B06）。

| 字段 | 类型 | 空 | 默认 | 说明 |
|---|---|---|---|---|
| `id` | INTEGER PK | 否 | 自增 | |
| `page_id` | INTEGER FK | 否 | | → `pages.id`，ON DELETE CASCADE |
| `version_no` | INTEGER | 否 | | 版本号（页内递增） |
| `created_by` | INTEGER | 是 | | 创建人 admin id（逻辑引用） |
| `created_at` | DATETIME | 否 | utcnow | |
| `note` | VARCHAR(200) | 是 | | 版本备注 |

**索引**：`ix_page_versions_page_id`。

### 4.8 `blocks` CMS 区块

**用途**：区块（11 种类型）挂在**版本**下，非页面下——保证回滚到旧版本时区块整体还原。

| 字段 | 类型 | 空 | 默认 | 说明 |
|---|---|---|---|---|
| `id` | INTEGER PK | 否 | 自增 | |
| `page_version_id` | INTEGER FK | 否 | | → `page_versions.id`，ON DELETE CASCADE |
| `type` | VARCHAR(20) | 否 | | 枚举 11 种区块类型 |
| `config_json` | JSON | 否 | `{}` | 内容与样式配置 |
| `sort` | INTEGER | 否 | 0 | 区块顺序 |
| `mobile_visible` | BOOLEAN | 否 | true | 移动端是否显示（FR-B08） |

**索引**：`ix_blocks_page_version_id`。

### 4.9 `contact_messages` 联系留言

**用途**：「联系我们」留言表单（FR-F86/F87），后台处理（pending/contacted/closed）。联系方式默认脱敏展示，明文仅超管可见。

| 字段 | 类型 | 空 | 默认 | 说明 |
|---|---|---|---|---|
| `id` | INTEGER PK | 否 | 自增 | |
| `name` | VARCHAR(100) | 否 | | 姓名 |
| `company` | VARCHAR(200) | 是 | | 公司/机构 |
| `contact_type` | VARCHAR(5) | 否 | | 枚举 phone/email（决定脱敏规则） |
| `contact` | VARCHAR(200) | 否 | | 手机或邮箱（脱敏存储/展示） |
| `coop_type` | VARCHAR(7) | 是 | | 枚举 hq/media/channel/invest |
| `content` | TEXT | 否 | | 留言内容 |
| `handle_status` | VARCHAR(9) | 否 | pending | 枚举 pending/contacted/closed |
| `handled_by` | INTEGER | 是 | | 处理人 admin id（逻辑引用） |
| `remark` | TEXT | 是 | | 处理备注 |
| `created_at` | DATETIME | 否 | utcnow | |

**索引**：`ix_contact_messages_handle_status`、`ix_contact_messages_created_at`。

### 4.10 `admin_users` 后台账号

**用途**：后台登录账号（JWT + RBAC）。角色用**枚举**实现轻量 RBAC（FR-B51~B54）。

| 字段 | 类型 | 空 | 默认 | 说明 |
|---|---|---|---|---|
| `id` | INTEGER PK | 否 | 自增 | |
| `username` | VARCHAR(100) | 否 | | **UNIQUE**，登录账号 |
| `password_hash` | VARCHAR(255) | 否 | | bcrypt 哈希，不存明文 |
| `role` | VARCHAR(15) | 否 | CONTENT_OPS | 枚举 SUPER_ADMIN/CONTENT_OPS/MERCH_STORE_OPS |
| `status` | VARCHAR(8) | 否 | active | 枚举 active/disabled |
| `last_login_at` | DATETIME | 是 | | 上次登录时间 |
| `failed_attempts` | INTEGER | 否 | 0 | 连续失败次数（FR-B54 锁定） |
| `locked_until` | DATETIME | 是 | | 锁定截止时间 |
| `created_at` | DATETIME | 否 | utcnow | |

**索引**：`ix_admin_users_username`(UNIQUE)。

### 4.11 `admin_login_logs` 登录日志

**用途**：登录审计——成功/失败/原因/IP（FR-B54）。

| 字段 | 类型 | 空 | 默认 | 说明 |
|---|---|---|---|---|
| `id` | INTEGER PK | 否 | 自增 | |
| `user_id` | INTEGER | 是 | | admin id（逻辑引用；登录失败可能无对应） |
| `username` | VARCHAR(100) | 否 | | 尝试登录的用户名（冗余快照） |
| `success` | BOOLEAN | 否 | false | 是否成功 |
| `fail_reason` | VARCHAR(100) | 是 | | 失败原因（如密码错误/锁定） |
| `ip` | VARCHAR(64) | 是 | | 来源 IP |
| `created_at` | DATETIME | 否 | utcnow | |

**索引**：`ix_admin_login_logs_user_id`、`ix_admin_login_logs_created_at`。

### 4.12 `operation_logs` 操作日志

**用途**：关键操作留痕——谁/何时/对什么/做了什么/变更前后摘要（FR-B10/B55）。

| 字段 | 类型 | 空 | 默认 | 说明 |
|---|---|---|---|---|
| `id` | INTEGER PK | 否 | 自增 | |
| `user_id` | INTEGER | 是 | | 操作人 admin id（逻辑引用） |
| `username` | VARCHAR(100) | 是 | | 操作人用户名（冗余快照） |
| `action_type` | VARCHAR(50) | 否 | | create/update/delete/publish… |
| `target_type` | VARCHAR(50) | 否 | | 操作对象类型（page/news/item/store…） |
| `target_id` | VARCHAR(64) | 是 | | 对象 id（字符以兼容各表） |
| `before` | TEXT | 是 | | 变更前摘要 |
| `after` | TEXT | 是 | | 变更后摘要 |
| `created_at` | DATETIME | 否 | utcnow | |

**索引**：`ix_operation_logs_user_id`、`ix_operation_logs_created_at`。

---

## 5. 索引设计汇总

| 表 | 索引 | 类型 | 支撑查询 |
|---|---|---|---|
| collections | `(category,status,published_at)` | 组合 | 品类页系列墙（FR-F21/F22） |
| items | `(is_hot,hot_sort)` | 组合 | 热门推荐页（FR-F23） |
| items | `collection_id` | 单列 | 系列→款式列表（FR-F25） |
| items | `item_code` | UNIQUE | 库存关联/详情 URL |
| stores | `city` | 单列 | 城市筛选/地图聚类（FR-F34） |
| store_stocks | `(store_id,item_code)` | UNIQUE | 去重导入（验收标准） |
| articles | `(category,status,published_at)` 拆分索引 | 单列+单列 | 新闻分类列表 |
| contact_messages | `handle_status` | 单列 | 后台留言处理列表 |
| admin_login_logs / operation_logs | `created_at` + `user_id` | 单列 | 后台日志筛选 |

> 数据量级（一期：≤20 门店、≤3 品类各 1 系列、每系列 ≤60 款式、新闻月更）对 SQLite 完全友好，无需分区/全文索引；全站搜索 FR-F71 使用 `LIKE` 即可（见 §6.2 待确认）。

---

## 6. SQLite 专项说明与注意点

### 6.1 SQLite 使用规范

1. **连接串**：`sqlite+aiosqlite:///./fly.db`（`backend/app/config.py` 默认值）；`echo=DB_ECHO` 控制 SQL 日志。
2. **并发模型**：官网是**读多写少**的内容站；前台读走 CDN + API，写仅在后台运营操作。SQLite 单写者限制在本量级下无压力。建议开启 **WAL** 模式提升读写并发（`PRAGMA journal_mode=WAL`）。
3. **外键**：默认关闭，业务级联依赖它，建议连接事件里 `PRAGMA foreign_keys=ON`（待确认项，见 6.2）。
4. **时间统一 UTC** 存储（`datetime.utcnow`），展示层转本地时间。
5. **布尔**：存 0/1；**JSON**：SQLAlchemy 序列化为文本存储，查询用 `LIKE` 或取出后程序过滤。
6. **备份（NFR-25）**：SQLite 备份 = 复制/导出 db 文件。每日任务可用 `sqlite3 fly.db ".backup 'backup/fly-$(date).db'"`（在线安全备份）或直接复制文件（须配合 WAL checkpoint）。保留 ≥30 天并定期演练恢复。备选方案 `python -m app.seed` 前先备份。

### 6.2 待确认项（需开发/评审确认）

| # | 事项 | 现状 | 建议 |
|---|---|---|---|
| Q1 | 外键 PRAGMA | `database.py` 未显式开启 | 在 engine connect 事件加 `PRAGMA foreign_keys=ON`，使 CASCADE 级联生效 |
| Q2 | WAL 模式 | 未开启 | 连接时 `PRAGMA journal_mode=WAL`（可选，看并发需求） |
| Q3 | 全站搜索实现 | 依赖 LIKE | 一期量级 OK；若内容量上来再评估 FTS5 |
| Q4 | 素材库表 | 不建表，URL 引用 | 二期如需"引用统计/删除保护"新增 `media_assets` 表（id/url/type/size/uploader/created_at） |
| Q5 | `collections.updated_at` | 商品表无更新时间戳 | 如需"最近更新"排序可补；一期无此需求可不加 |
| Q6 | `page_versions.version_no` 并发唯一 | 依赖应用层递增 | 同一 page 下并发建版本需锁或唯一约束 (page_id, version_no)，一期后台单运营编辑可接受 |

### 6.3 预留与二期扩展位（不本期实现）

- `items.ext_json`：SKU/尺码等二期电商扩展（FR-B27）——**已预留**，本期前台不消费（价格字段已于 v1.1 独立为 `items.price` 列，见下）
- `items.price`（v1.1 记录字段）：吊牌/参考零售价（元），已在建表 DDL 落地为独立列；**后端本期不读写、前台不展示**，ORM 未映射——启用需在模型补列并迁移，属二期，非本期实现项
- 素材库 `media_assets` 表：素材元数据（见 Q4）
- 会员/交易/预约表：属 Backlog，本文档不展开

---

## 附录 A：完整建表 DDL

> 基础由 `backend/.venv` 内 SQLAlchemy 2.0.52 方言编译导出，与模型 100% 一致。**唯一例外**：`items.price`（记录字段，ORM 未映射）为 v1.1 手工补入，脚本内已注释标注。文件：`docs/FLY官网_SQLite建表DDL.sql`。

```sql
-- 关键结构预览（完整版见 DDL 文件）：
-- 1) collections / items：商品域，items.collection_id FK CASCADE
-- 2) stores / store_stocks：门店域，uq_store_item UNIQUE(store_id,item_code)
-- 3) pages / page_versions / blocks：CMS 域，版本快照 + 区块
-- 4) articles / contact_messages：内容/留言
-- 5) admin_users / admin_login_logs / operation_logs：账号与日志
```

---

## 附录 B：与 PRD 第 10 章的差异说明

| 项 | PRD 10.2 表述 | 实际落地（本文档） | 说明 |
|---|---|---|---|
| 数据库 | PostgreSQL（v1.4 技术栈） | **SQLite** | v1.5 决策变更 |
| `Role` | 实体/role_id FK | **枚举列** `admin_users.role` | 轻量 RBAC 三角色固定，不建 roles 表 |
| `Category` | 概念枚举 | **不建表**，`collections.category` 枚举列 | 品类不是实体表 |
| 库存关联 | `item_code` FK | 逻辑引用 + 应用层校验 | 有意设计（见 §3.3） |
| `Item` 价格 | `price` decimal(10,2) 可空（v1.6 新增） | **独立列 `price` NUMERIC(10,2)（记录字段）** | v1.6/v1.1 变更：品牌方要求款式主数据含价格；后端本期不读写、前台不展示（N5 不变），ORM 未映射（见 §4.2） |
| 素材库 | FR-B16 素材集中管理 | 不建表，URL 引用 + `uploads/` 磁盘 | 一期磁盘，二期 OSS |
