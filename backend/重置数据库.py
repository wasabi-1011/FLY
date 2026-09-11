# -*- coding: utf-8 -*-
"""数据库重置工具：把 fly.db 恢复为「初始状态」，方便反复测试后随时复原。

用法（在 backend 目录下执行）：
    python 重置数据库.py             # 恢复初始状态（推荐）
    python 重置数据库.py --show       # 只看当前库 / 快照的状态，不改动
    python 重置数据库.py --seed       # 只重灌 9 条新闻种子（保留其余数据）
    python 重置数据库.py --snapshot   # 把当前库另存为新的初始快照（更新基准，慎用）

原理：
    初始基准 = backend/初始数据/初始数据库.db
      （干净初始态：3 个账号 / 7 个页面 / 首页 7 个区块含 4 帧轮播 / 9 条新闻 /
        8 款式 + 8 系列（商品域 v2.2 起种子）/ 0 留言 / 无运行日志）
    重置 = 用基准整体覆盖 fly.db（走 SQLite backup API，保证一致性）。
    若基准文件缺失，则用内置初始数据现场重建（表结构 + 账号 + 首页区块 + 9 条新闻）。

注意：
    重置前请先停止后端服务（双击「启动.bat」选 4），否则数据库文件被占用会失败。
"""
from __future__ import annotations

import argparse
import asyncio
import json
import socket
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

DB = BACKEND_DIR / "fly.db"
SNAP_DIR = BACKEND_DIR / "初始数据"
SNAP = SNAP_DIR / "初始数据库.db"

TABLES = [
    "admin_users", "admin_login_logs", "operation_logs", "contact_messages",
    "articles", "blocks", "page_versions", "pages",
    "collections", "items", "store_stocks", "stores",
]


# ---------------------------------------------------------------- 基础工具
def counts(path) -> dict | None:
    path = Path(path)
    if not path.exists():
        return None
    conn = sqlite3.connect(str(path))
    out = {}
    try:
        for t in TABLES:
            try:
                out[t] = conn.execute(f"select count(*) from {t}").fetchone()[0]
            except Exception:
                out[t] = "-"
    finally:
        conn.close()
    return out


def brief(c: dict | None) -> str:
    if not c:
        return "(不存在)"
    keys = ["pages", "blocks", "articles", "items", "collections", "admin_users", "contact_messages"]
    return " | ".join(f"{k}={c.get(k, '-')}" for k in keys)


def port_busy(port: int = 8000) -> bool:
    s = socket.socket()
    s.settimeout(0.4)
    try:
        s.connect(("127.0.0.1", port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def backup(src: Path, dst: Path) -> None:
    """SQLite 在线备份：src -> dst（一致性快照）。"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    src_conn = sqlite3.connect(str(src))
    dst_conn = sqlite3.connect(str(dst))
    try:
        src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()


# ---------------------------------------------------------------- 各模式
def show() -> None:
    print("当前库   :", DB)
    print("            ", brief(counts(DB)))
    print("初始快照 :", SNAP)
    print("            ", brief(counts(SNAP)))
    print()
    print("提示：重置 = 用初始快照覆盖当前库。执行前请先停止后端服务。")


def do_snapshot() -> None:
    if not DB.exists():
        print("当前库不存在，无法制作快照。")
        sys.exit(1)
    backup(DB, SNAP)
    print("已把当前库保存为初始快照：")
    print("  ", SNAP)
    print("  ", brief(counts(SNAP)))


def do_seed() -> None:
    """只重灌 9 条新闻种子（调用 种子数据.py 的逻辑）。"""
    import importlib.util

    seed_path = BACKEND_DIR / "种子数据.py"
    spec = importlib.util.spec_from_file_location("fly_seed", str(seed_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    mod.asyncio.run(mod.run(append=False, dry=False))
    print("  ", brief(counts(DB)))


def restore() -> None:
    if port_busy(8000):
        print("!! 检测到后端服务仍在运行（端口 8000 被占用）。")
        print("   请先停止服务（双击「启动.bat」选 4），再执行重置。")
        print("   继续尝试中 ...\n")
    try:
        if SNAP.exists():
            backup(SNAP, DB)
            print("已从初始快照恢复当前库：")
            print("  ", DB)
        else:
            print("未找到初始快照，改用内置初始数据现场重建 ...")
            asyncio.run(rebuild_minimal())
        print("\n完成。恢复后状态：")
        print("  ", brief(counts(DB)))
        print("\n现在可以双击「启动.bat」选 1 启动，数据已回到初始状态。")
    except (sqlite3.OperationalError, PermissionError) as e:
        print("\n重置失败：", e)
        print("原因通常是后端服务仍占用数据库文件。请停止服务后重试。")
        sys.exit(1)


# ---------------------------------------------------------------- 兜底重建
HOME_FRAMES = [
    {"image": "/uploads/0553a5faa5fa47c0a3f5c899c086b736.jpg", "kicker": "", "title": "FLY",
     "sub": "穿出自我，随心而飞", "cn": "", "link": "/products", "active": True,
     "layers": [{"text": "FLY", "style": "brand-wordmark"}, {"text": "穿出自我，随心而飞", "style": "en-sub"}]},
    {"image": "/uploads/0aac94d4fa46486ea32416a9c46f0a0f.jpg", "kicker": "", "title": "城野机能",
     "sub": "城市与山野，同频共振", "cn": "", "link": "/products/men", "active": True,
     "layers": [{"text": "城野机能", "style": "brand-wordmark"}, {"text": "城市与山野，同频共振", "style": "en-sub"}]},
    {"image": "/uploads/15903a3a02714b689be247c93cb4d99d.png", "kicker": "", "title": "拥抱自然",
     "sub": "穿出自我，随心而飞", "cn": "", "link": "/products", "active": True,
     "layers": [{"text": "拥抱自然", "style": "brand-wordmark"}, {"text": "穿出自我，随心而飞", "style": "en-sub"}]},
    {"image": "/uploads/aac54efabc0b47259b5eb71b60d9f53b.png", "kicker": "", "title": "自由FLY",
     "sub": "时尚 源于专业", "cn": "", "link": "/products", "active": True,
     "layers": [{"text": "自由FLY", "style": "brand-wordmark"}, {"text": "时尚 源于专业", "style": "en-sub"}]},
]

FIXED_PAGES = [
    ("about/fly", "关于 FLY"), ("about/brand", "品牌介绍"), ("about/history", "发展历程"),
    ("about/contact", "联系我们"), ("join/social", "社会招聘"), ("join/campus", "校园招聘"),
]


async def rebuild_minimal() -> None:
    """初始快照缺失时的兜底：建表 + 3 账号 + 首页/固定页 + 9 条新闻 + 8 款式/8 系列。"""
    import importlib.util

    from app import models  # noqa: F401  注册全部模型
    from app.database import SessionLocal, engine
    from app.enums import AdminStatus, BlockType, PageStatus, Role
    from app.models.admin import AdminUser
    from app.models.base import Base
    from app.models.content import Block, Page, PageVersion
    from app.security import hash_password

    # 1) 重建表结构
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("  已重建表结构。")

    # 2) 账号
    async with SessionLocal() as db:
        db.add_all([
            AdminUser(username="admin", password_hash=hash_password("admin1234"), role=Role.SUPER_ADMIN, status=AdminStatus.ACTIVE),
            AdminUser(username="editor", password_hash=hash_password("editor1234"), role=Role.CONTENT_OPS, status=AdminStatus.ACTIVE),
            AdminUser(username="merch", password_hash=hash_password("merch1234"), role=Role.MERCH_STORE_OPS, status=AdminStatus.ACTIVE),
        ])
        await db.commit()
    print("  已创建 3 个账号（admin / editor / merch，密码为用户名 + 1234）。")

    # 3) 页面与区块
    async with SessionLocal() as db:
        for slug, title in FIXED_PAGES:
            p = Page(slug=slug, title=title, page_type="fixed", status=PageStatus.PUBLISHED)
            db.add(p)
            await db.flush()
            v = PageVersion(page_id=p.id, version_no=1, note="初始版本")
            db.add(v)
            await db.flush()
            p.current_version_id = v.id
            db.add(Block(page_version_id=v.id, type=BlockType.RICH_TEXT, config_json={"html": ""}, sort=0))

        home = Page(slug="home", title="首页", page_type="fixed", status=PageStatus.PUBLISHED)
        db.add(home)
        await db.flush()
        hv = PageVersion(page_id=home.id, version_no=1, note="初始版本")
        db.add(hv)
        await db.flush()
        home.current_version_id = hv.id
        for i, (bt, cfg) in enumerate([
            (BlockType.FULLSCREEN_VISUAL, {"autoplay": 5, "frames": HOME_FRAMES}),
            (BlockType.IMAGE_BANNER, {"image": "https://cdn.example.com/banner.jpg", "link": "/products/men"}),
            (BlockType.COLLECTION_RECOMMEND, {"title": "当季系列"}),
            (BlockType.HOT_RECOMMEND, {"title": "热门推荐", "count": 8}),
            (BlockType.STORE_ENTRY, {"title": "寻找门店", "cities_count": 8, "stores_count": 20}),
            (BlockType.NEWS_RECOMMEND, {"title": "品牌动态"}),
            (BlockType.COLUMN_ENTRY, {"title": "快速导航"}),
        ]):
            db.add(Block(page_version_id=hv.id, type=bt, config_json=cfg, sort=i))
        await db.commit()
    print("  已创建 6 个固定页 + 首页（含 4 帧轮播区块）。")

    # 4) 新闻种子
    spec = importlib.util.spec_from_file_location("fly_seed", str(BACKEND_DIR / "种子数据.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    await mod.run(append=False, dry=False)

    # 5) 商品域种子（5 款式 + 8 系列，图片取 /pic/item-*.jpg 与 /pic/series-*.jpg）
    pspec = importlib.util.spec_from_file_location(
        "fly_seed_product", str(BACKEND_DIR / "种子数据_商品.py")
    )
    pmod = importlib.util.module_from_spec(pspec)
    pspec.loader.exec_module(pmod)  # type: ignore[union-attr]
    await pmod.run(dry=False, append=False)


# ---------------------------------------------------------------- 入口
def main() -> None:
    ap = argparse.ArgumentParser(description="把数据库恢复为初始状态")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--show", action="store_true", help="只查看状态")
    g.add_argument("--seed", action="store_true", help="只重灌 9 条新闻种子")
    g.add_argument("--snapshot", action="store_true", help="把当前库另存为初始快照")
    args = ap.parse_args()

    print("=" * 52)
    print("  FLY 数据库重置工具")
    print("=" * 52)
    if args.show:
        show()
    elif args.seed:
        do_seed()
    elif args.snapshot:
        do_snapshot()
    else:
        restore()


if __name__ == "__main__":
    main()
