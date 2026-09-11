# -*- coding: utf-8 -*-
"""商品域结构迁移 v2：品类 → 款式 → 系列（系列从「款式的父级」改为「款式的子级」）。

背景：
    旧结构 collections(系列, 自带 category) ← items(款式, collection_id 外键)
    新结构 items(款式, 自带 category) → collections(系列, item_id 外键, 选填 0..n)

    因为外键方向反转，SQLite 无法直接改列，采用「读出数据 → 重建两张表 → 回填」的方式，
    不依赖 RENAME（避免 SQLite 自动改写其它表的外键引用）。

能保留的：
    items 全部字段（款式数据不丢），并把它原来所属系列的 category 回填为 item.category。
无法保留的：
    collections 旧数据（系列原本是款式的父级，逻辑上无法映射到新的子级关系），会被清空；
    新的系列数据由 `种子数据_商品.py` 灌入。

幂等：若 items 已含 category 列，直接跳过。

用法（在 backend 目录下执行，且先停止后端服务）：
    python 迁移_商品域v2.py --dry-run   # 只看会发生什么
    python 迁移_商品域v2.py             # 执行
"""
from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
DB = BACKEND_DIR / "fly.db"

ITEM_COLS = (
    "id, item_code, name, category, is_hot, hot_sort, images, video_url, fabric, "
    "colors, fit_description, description, sort_weight, status, ext_json"
)

DDL_ITEMS = """
CREATE TABLE items (
    id INTEGER NOT NULL,
    item_code VARCHAR(64) NOT NULL,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(5) NOT NULL,
    is_hot BOOLEAN NOT NULL,
    hot_sort INTEGER NOT NULL,
    images JSON,
    video_url VARCHAR(512),
    fabric VARCHAR(300),
    colors JSON,
    fit_description VARCHAR(300),
    description TEXT,
    sort_weight INTEGER NOT NULL,
    status VARCHAR(7) NOT NULL,
    ext_json JSON,
    PRIMARY KEY (id)
)
"""

DDL_COLLECTIONS = """
CREATE TABLE collections (
    id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    name VARCHAR(200) NOT NULL,
    year INTEGER,
    season VARCHAR(13),
    cover_image VARCHAR(512),
    status VARCHAR(7) NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(item_id) REFERENCES items (id) ON DELETE CASCADE
)
"""

DDL_INDEXES = [
    "CREATE UNIQUE INDEX ix_items_item_code ON items (item_code)",
    "CREATE INDEX ix_items_category ON items (category)",
    "CREATE INDEX ix_items_status ON items (status)",
    "CREATE INDEX ix_items_is_hot ON items (is_hot)",
    "CREATE INDEX ix_item_cat_status ON items (category, status)",
    "CREATE INDEX ix_item_hot ON items (is_hot, hot_sort)",
    "CREATE INDEX ix_collections_item_id ON collections (item_id)",
    "CREATE INDEX ix_collections_status ON collections (status)",
]


def has_column(cur: sqlite3.Cursor, table: str, col: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return any(r[1] == col for r in cur.fetchall())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not DB.exists():
        print(f"[跳过] 未找到数据库：{DB}")
        return

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    if has_column(cur, "items", "category"):
        print("[跳过] items 已含 category 列，数据库已是 v2 结构。")
        conn.close()
        return

    # 1) 读出旧数据（在删表之前）
    cur.execute("SELECT id, category FROM collections")
    cat_by_col = {cid: cat for cid, cat in cur.fetchall()}
    cur.execute(
        "SELECT id, item_code, name, collection_id, is_hot, hot_sort, images, video_url, "
        "fabric, colors, fit_description, description, sort_weight, status, ext_json FROM items"
    )
    rows = cur.fetchall()
    print(f"读取到 {len(rows)} 条款式、{len(cat_by_col)} 个旧系列。")

    new_items = []
    for r in rows:
        (iid, code, name, col_id, is_hot, hot_sort, images, video_url, fabric, colors,
         fit, desc, sort_w, status, ext) = r
        cat = cat_by_col.get(col_id) or "MEN"  # 兜底：旧数据缺失时归男装
        new_items.append((iid, code, name, cat, is_hot, hot_sort, images, video_url,
                         fabric, colors, fit, desc, sort_w, status, ext))
    print(f"  其中 {sum(1 for c in cat_by_col.values() if c)} 个旧系列的品类已用于回填 category。")

    if args.dry_run:
        print("[dry-run] 将重建 items / collections 两张表并回填 category，未落库。")
        conn.close()
        return

    # 2) 备份（同目录，带时间戳）
    backup = BACKEND_DIR / f"fly.db.bak-{datetime.now():%Y%m%d%H%M%S}"
    shutil.copy2(DB, backup)
    print(f"已备份原库 → {backup.name}")

    # 3) 重建
    cur.execute("PRAGMA foreign_keys=OFF")
    cur.execute("DROP TABLE IF EXISTS collections")
    cur.execute("DROP TABLE IF EXISTS items")
    cur.execute(DDL_ITEMS)
    cur.execute(DDL_COLLECTIONS)
    cur.executemany(
        f"INSERT INTO items ({ITEM_COLS}) VALUES ({','.join('?' * 15)})", new_items
    )
    for ddl in DDL_INDEXES:
        cur.execute(ddl)
    conn.commit()
    conn.close()
    print("迁移完成：items 保留并新增 category；collections 已重建为空（待灌种子数据）。")


if __name__ == "__main__":
    sys.exit(main())
