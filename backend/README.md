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

### 内容运营·新闻/资讯（已与后台原型、前台新闻页打通）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/admin/news` | 后台列表，支持 `category` / `status` / `keyword` |
| POST | `/api/admin/news` | 新建（`slug` 唯一，重名 409） |
| GET | `/api/admin/news/{id}` | 详情 |
| PUT | `/api/admin/news/{id}` | 更新（正文经 `sanitize_html`） |
| DELETE | `/api/admin/news/{id}` | 删除 |
| GET | `/api/news` | 前台列表（仅 `status=online`，按 `published_at` 倒序，分页） |
| GET | `/api/news/{category}/{slug}` | 前台详情（非 online 返回 404） |

- 分类枚举 `NewsCategory`：**固定 `company` / `industry` 两项**（对齐 PRD FR-F54），不提供后台增删。
- 发布语义：`status=online` 即发布；**若未传 `published_at`，后端自动填当前时间**（新建与草稿转发布皆如此），避免前台排序掉末尾。
- 字段：`cover_image`（封面）、`summary`（列表摘要）、`content`（富文本 HTML）、`author`、`seo_*`。
- 链路：**后台原型 → 本接口写 `articles` 表 → 前台 `GET /api/news*` → NewsList/NewsDetail/首页渲染**。
- 前台取数策略（v1.6）：接口**成功但为空** → 显示空状态；**接口失败** → 才回退本地 `siteData` 兜底并在页头提示。首页与 `/news` 同源。
- 删除返回 **204 No Content**（响应头带 `content-type: application/json` 但无 body）；调用方需按 204 处理，不要对空体做 JSON 解析（后台原型 `apiCall` 已处理）。

### 留言管理（已与前台表单、后台原型打通）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/admin/contacts` | 列表，支持 `handle_status` / `keyword` / `include_deleted`，**默认排除已删除** |
| PATCH | `/api/admin/contacts/{id}` | 处理动作：`handle_status`（pending/contacted/closed）+ `remark`（内部处理记录） |
| DELETE | `/api/admin/contacts/{id}` | **软删除**（置 `is_deleted=1`，数据保留可审计） |
| POST | `/api/contact` | 前台公开提交（IP 限频，无需登录） |

- 「回复」在本阶段 = **内部处理备注**，不向用户发送邮件/短信（真实触达列为二期）。
- 脱敏：列表/详情默认返回 `contact_masked`，仅 `SUPER_ADMIN` 额外拿到 `contact_full`。
- 链路：**前台 `/contact` 提交 → `contact_messages` 表 → 后台「留言管理」连接后可见/处理/删除**。

## 种子数据（新闻初始内容）

`backend/种子数据.py` 把**前端默认新闻**（`frontend/web/src/data/siteData.js` 的 `NEWS`，9 条 = 5 企业 + 4 行业）灌入 `articles` 表，使「数据库 / 后台 / 首页 / 新闻列表」取得**初始一致性**。

```bash
python 种子数据.py            # 清空 articles 后写入 9 条（幂等，推荐）
python 种子数据.py --append   # 不清空，仅追加库中缺失的 slug
python 种子数据.py --dry-run  # 只预览将写入的内容，不落库
```

- 用 Node 动态 `import` 前端 `siteData.js` 提取 `NEWS`，避免手写重复数据漂移；需本机已安装 Node（前台构建也依赖它）。
- 结构化正文（`p/h/quote/img`）转 HTML，标签与前台详情页渲染器一致：`<p>` / `<h3>` / `<blockquote>` / `<figure class="art-fig">`。
- 直接经 ORM 写库，绕过后台接口的富文本净化；生成内容自身安全（全部转义）。
- 默认先清空 `articles` 再写入，重复执行结果一致。

## 数据库字段变更（轻量迁移）

项目未引入 Alembic，新增列时用 `backend/轻量迁移.py` 幂等补齐：

```bash
python 轻量迁移.py
```

已登记：`contact_messages.is_deleted`（BOOLEAN DEFAULT 0，留言软删除）。以后加列在脚本顶部 `MIGRATIONS` 追加一行 `(表名, 列名, DDL)` 即可。

## 数据库重置（初始数据）

测试会反复增删数据，需要随时回到干净初始态：

```bash
python 重置数据库.py            # 用初始快照覆盖 fly.db（推荐）
python 重置数据库.py --show      # 只看当前库 / 快照状态，不改动
python 重置数据库.py --seed      # 只重灌 9 条新闻种子（保留其余数据）
python 重置数据库.py --snapshot  # 把当前库另存为新的初始快照（更新基准，慎用）
```

- 初始基准：`backend/初始数据/初始数据库.db`（含 3 账号 / 7 页面 / 首页 4 帧轮播 / 9 条新闻 / 20 门店 / 16 款式 / 4 系列）。**这是权威基准，请勿删除。**
- 覆盖走 **SQLite backup API**（一致性快照），不是简单文件拷贝；基准缺失时会现场兜底重建（建表 + 账号 + 固定页 + 首页区块 + 9 条新闻），但**不含门店/款式/系列演示数据**，所以基准文件仍需保留。
- **执行前请先停止后端服务**（`启动.bat` 选 4），否则数据库文件被占用会失败。脚本会检测 8000 端口占用并提示。
- 启动脚本 `启动.bat` / `start.bat` 的菜单项 **5** 已内置「先停服务再重置」，**6** 为「查看数据库状态」。

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
