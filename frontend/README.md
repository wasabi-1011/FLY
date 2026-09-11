# FLY 品牌官网 · 前端

前后台拆成两个独立 React 应用（对应 PRD「前台 SSR + 后台 SPA」决定）：

| 目录 | 说明 | 默认端口 |
|---|---|---|
| `web/` | **前台**（品牌官网，React，SSR 预留，SEO 关键） | 3000 |
| `admin/` | **后台**（管理端，React SPA + Ant Design） | 5173 |
| `web/static/` | 静态参考资源（HTML 原型 + `pic/` 图片素材库） | — |

## 目录结构

```
frontend/
├── README.md
├── web/                  # 前台
│   ├── index.html
│   ├── vite.config.js    # /api → localhost:8000 代理
│   ├── package.json
│   └── src/
│       ├── main.jsx
│       ├── App.jsx       # 路由骨架（/、/products、/stores…）
│       ├── pages/        # Home / Products / Stores …
│       ├── components/   # 导航 / 页脚 / 轮播 / 门店入口 …
│       ├── data/         # 取数层（含 tmapLoader.js：腾讯地图 SDK 单例加载）
│       └── styles/
├── web/public/pic/       # 前台运行时图片 36 张 jpg（banner/hot/item/series/storefront…）
│                         # + 静态数据 geo-china.json、echarts.min.js；母版 PNG 在 D:\FLY网站\picTest\
├── admin/                # 后台（另有原型页 backendManage/index.html，未走本目录）
│   ├── index.html
│   ├── vite.config.js    # /api → localhost:8000 代理
│   ├── package.json
│   └── src/
│       ├── main.jsx
│       ├── App.jsx       # 鉴权路由 + Ant Design 布局
│       └── pages/        # Login / Dashboard …
└── web/static/           # 静态参考（原型，仅 html）
    ├── FLY官网_首页原型.html   # F1 首页视觉原型
    └── FLY门店地图.html        # 门店地图原型
```

## 与后端的联调

两者 `vite.config.js` 均把 `/api` 代理到 `http://localhost:8000`（FastAPI 后端，见 `D:/FLY网站/backend`）。
开发时先起后端，再起前端：

```bash
# 1. 后端
cd D:\FLY网站\backend && uvicorn app.main:app --reload --port 8000

# 2. 前台
cd D:\FLY网站\frontend\web && npm install && npm run dev   # http://localhost:3000

# 3. 后台
cd D:\FLY网站\frontend\admin && npm install && npm run dev # http://localhost:5173
```

## frontend 边界说明

- `web/static/` 里的 HTML 原型是**静态参考页**（直接从浏览器打开即可见效果），供开发对照；
  真正的线上页面应由 `web/` React 工程按 CMS `/api/content/home` 等接口渲染。
- `pic/` 图片素材在本仓库为本地引用；上线时应由后台 CMS 上传并走 CDN（PRD v1.4 图片素材放后台管理）。
- 门店坐标、图片为占位/示例，上线前由零售运营补充实测值（FR-F45）。
