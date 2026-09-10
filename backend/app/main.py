"""FastAPI 应用入口：装配路由、CORS、启动建表。"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers.public import contact, home, news, pages, products, search, stores
from app.routers.admin import (
    admin_users,
    auth,
    collections,
    contacts,
    dashboard,
    items,
    news as admin_news,
    pages as admin_pages,
    stores as admin_stores,
    upload,
    home as admin_home,
)

PUBLIC_ROUTERS = [
    home.router,
    products.router,
    stores.router,
    news.router,
    pages.router,
    search.router,
    contact.router,
]
ADMIN_ROUTERS = [
    auth.router,
    collections.router,
    items.router,
    admin_stores.router,
    admin_news.router,
    admin_pages.router,
    contacts.router,
    admin_users.router,
    dashboard.router,
    upload.router,
    admin_home.router,
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="FLY 品牌官网后端 API（FastAPI）。前台公开读接口 + 后台管理（JWT/RBAC）。",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "service": settings.PROJECT_NAME}


for r in PUBLIC_ROUTERS + ADMIN_ROUTERS:
    app.include_router(r)

# ---------------- 静态资源挂载 ----------------
# backend/ 目录：uploads（后台上传的图片）与 ../backendManage（后台管理原型单页）
BACKEND_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BACKEND_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

ADMIN_DIR = BACKEND_DIR.parent / "backendManage"
if ADMIN_DIR.is_dir():
    app.mount("/admin", StaticFiles(directory=str(ADMIN_DIR), html=True), name="admin")


@app.get("/", tags=["meta"], include_in_schema=False)
async def index():
    """根路径导航：避免访问 http://localhost:8000 时看到 404。"""
    return {
        "service": settings.PROJECT_NAME,
        "docs": "/docs",
        "health": "/health",
        "admin": "/admin/index.html" if ADMIN_DIR.is_dir() else None,
        "tip": "这是纯 API 服务，没有根页面；后台管理界面请访问 /admin/index.html",
    }
