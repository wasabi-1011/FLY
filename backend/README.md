# FLY 品牌官网 · 后端（FastAPI）

依据 `docs/FLY品牌官网_PRD_v1.0.md`（v1.4 评审版）实现的品牌展示官网后端。
纯品牌展示定位：**无交易、无会员、无 SKU**，前台全部 SSR（由前端承担），后端提供
内容/商品/门店/库存/CMS/账号的完整 API 与 JWT + RBAC 鉴权。

## 技术栈

| 层 | 选型 |
|---|---|
| Web 框架 | FastAPI（异步，原生 OpenAPI） |
| ORM | SQLAlchemy 2.0（异步） |
| 数据库 | **SQLite（async，aiosqlite，单文件开箱即跑）** — v1.5 定稿统一使用 SQLite |
| 缓存/会话 | Redis（可选；未配置时限频降级为内存实现，非必选） |
| 鉴权 | JWT（python-jose）+ bcrypt 密码哈希 |
| 富文本安全 | bleach 白名单过滤（NFR-18 XSS 防护） |

> 生产部署建议：SQLite（开启 WAL/每日备份，见《数据库设计技术文档》）+ CDN；Redis 按需启用。

## 目录结构

```
app/
├── main.py                # 应用入口：CORS / 路由装配 / 启动建表
├── config.py              # pydantic-settings 配置
├── database.py            # 异步引擎 / 会话 / init_db
├── security.py            # 密码哈希 / JWT
├── dependencies.py        # get_db / get_current_user / require_roles
├── enums.py               # 全部共享枚举（品类/状态/角色/区块类型…）
├── models/                # 数据模型（10.2 章）
│   ├── product.py         # Collection / Item
│   ├── store.py           # Store / StoreStock
│   ├── content.py         # Page / PageVersion / Block / Article
│   ├── contact.py         # ContactMessage
│   └── admin.py           # AdminUser / AdminLoginLog / OperationLog
├── schemas/               # Pydantic 请求/响应模型
├── services/              # audit / ratelimit / sanitize
├── routers/
│   ├── public/            # 前台公开读接口（无需鉴权）
│   └── admin/             # 后台管理接口（JWT + RBAC）
└── seed.py                # 示例数据（门店/系列/款式/新闻/页面/账号）
```

## 快速开始

```bash
cd D:\FLY网站\backend

# 1. 安装依赖（建议虚拟环境）
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt

# 2. 准备配置（默认 SQLite，无需改）
cp .env.example .env

# 3. 灌示例数据（自动建表 + 写入示例内容）
python -m app.seed

# 4. 启动
uvicorn app.main:app --reload --port 8000
```

启动后访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health
- 后台管理界面：http://localhost:8000/admin/index.html （静态挂载 `../backendManage`）
- 上传的图片：http://localhost:8000/uploads/<文件名>（目录 `backend/uploads`，首次启动自动创建）

> 根路径 `http://localhost:8000/` 返回导航 JSON（本服务是纯 API，没有根页面）。

### 默认账号（seed 生成，上线前务必修改密码/停用示例账号）

| 账号 | 密码 | 角色 |
|---|---|---|
| admin | admin1234 | 超级管理员（R1） |
| editor | editor1234 | 内容运营（R2） |
| merch | merch1234 | 商品门店运营（R3） |

## 接口概览

### 前台公开（无需鉴权，对应 PRD 10.3）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/content/home` | 首页已发布区块配置 |
| GET | `/api/products/{category}` | 品类页（系列墙 + 热门） |
| GET | `/api/products/hot` | 热门推荐（`?category=` 二次筛选） |
| GET | `/api/products/{category}/{collection_slug}` | 系列详情 |
| GET | `/api/products/{category}/{collection_slug}/{item_code}` | 款式详情 |
| GET | `/api/stores/cities` | 有门店的城市与数量 |
| GET | `/api/stores` | 门店列表 + 地图点位（`?city`/`?type`） |
| GET | `/api/stores/{id}` | 门店详情 |
| GET | `/api/stores/availability?item_code=` | 有货城市（仅城市名） |
| GET | `/api/news` | 新闻列表（`?category=`） |
| GET | `/api/news/{category}/{slug}` | 新闻详情 |
| GET | `/api/pages/{full_path:path}` | 固定页/专题页（about/*、join/*、campaign/*） |
| GET | `/api/search?q=` | 全站搜索 |
| POST | `/api/contact` | 留言提交（限频 + 验证码占位） |

### 后台（JWT + RBAC，前缀 `/api/admin`）

- `auth/login`、`auth/me`
- `collections`、`items`（R3 商品门店运营）
- `stores` + `stores/stock/import`、`stores/stock/list`（R3，库存内部工具）
- `news`（R2 内容运营，正文 XSS 过滤）
- `pages`（CMS：版本/发布/回滚/并发锁，R2）
- `contacts`（R2，明文仅超管可见）
- `users`（超管，账号/角色/状态）
- `dashboard/stats`、`operation-logs`
- `upload`（图片上传，R2+；返回 `{"url": "/uploads/xxx.jpg"}`）
- `home/carousel`（首页轮播专用读写，R2+，见下）

鉴权：登录拿 `access_token`，后续请求头 `Authorization: Bearer <token>`。

### 首页轮播（已与后台原型、前台首页打通）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/admin/home/carousel` | 读取 home 当前版本 `FULLSCREEN_VISUAL` 区块，输出归一化 `frames[]` |
| PUT | `/api/admin/home/carousel` | 以当前版本为底新建 `PageVersion`，替换轮播区块并**立即发布**（写审计日志） |
| GET | `/api/content/home` | 前台公开读取（只应渲染 `active !== false` 的帧） |

frame 结构：`{ image, kicker, title, sub, cn, link, active }`（`image` 通常来自 `/api/admin/upload`）。
- `sub` = 轮播副标题（标题下方那行中文文案，后台新增时默认「穿出自我，随心而飞」）；
- `link` 为空时，前台「了解更多」按钮默认跳 `/products`（按钮恒定显示）。

链路：**后台原型保存 → 本接口写 fly.db → 前台 `GET /api/content/home` → 首页 Hero 渲染**。

**轮播数据在库里的位置**

```
pages(slug='home').current_version_id            ← 当前生效版本指针
  └─ page_versions(id, version_no)               ← 每次保存新建并发布一个版本（旧版本保留，可回滚）
       └─ blocks(type='FULLSCREEN_VISUAL').config_json.frames   ← 轮播帧数组
```

- 图片本体不入库，只存路径字符串 `/uploads/<uuid>.jpg`，文件在 `backend/uploads/`。
- 因每次保存都新建版本，`blocks` 表会有多份历史轮播数据，**只有 `current_version_id` 指向的那份显示在前台**；用数据库工具查看若"没变化"，先刷新查询结果。
- 一键查看：`python 查看首页轮播.py`（加 `--all` 列出所有历史版本），会打印三级定位、每帧字段，并校验图片文件是否真实存在。

## 与 PRD 的对应关系（要点）

- **Non-goals 严守**：款式详情/热门推荐**不含价格、库存、尺码、销量字样**（N5/N12）。
- **品类枚举固定** men/women/kids，不可后台增删（FR-B28）。
- **热门推荐** `is_hot` 纯人工标记，数据模型不支持自动计算（N12）。
- **CMS 11 种区块**、版本管理（≥10 版）、发布/回滚、并发编辑锁（FR-B02/B06/B03）。
- **门店坐标**为 GCJ-02；本 seed 坐标为占位值，上线前替换为实测坐标（FR-F45）。
- **富文本 XSS** 存储前后均经 bleach 白名单过滤（NFR-18）。
- **留言脱敏**：列表/详情默认脱敏，明文仅超管可见（FR-B19/NFR-22）。

## 已知工程取舍（本期）

- 验证码：留言接口保留 `captcha_token` 入参但未接验证服务，待接入（FR-F87）。
- 并发编辑锁为软锁（30 分钟 TTL），由前端在打开编辑页时 acquire。
- 缓存/限频为**可选优化**：配置 Redis 则使用；未配置时自动降级为单实例内存实现（开发期够用）。
- 生产应使用 Alembic 做迁移，而非 `init_db()` 的 `create_all`。
