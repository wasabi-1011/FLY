"""轻量迁移：幂等补齐 SQLite 缺失列（无 Alembic，开发期使用）。

用法：python 轻量迁移.py
每次新增模型字段后，在 MIGRATIONS 里追加一条 (表名, 列名, DDL 类型定义) 即可。
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent / "fly.db"

# (表名, 列名, ADD COLUMN 的 DDL 片段)
MIGRATIONS: list[tuple[str, str, str]] = [
    ("contact_messages", "is_deleted", "BOOLEAN DEFAULT 0"),
]


def column_exists(cur: sqlite3.Cursor, table: str, col: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == col for row in cur.fetchall())


def main() -> None:
    if not DB.exists():
        print(f"[跳过] 未找到数据库：{DB}")
        return
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    for table, col, ddl in MIGRATIONS:
        try:
            if column_exists(cur, table, col):
                print(f"[已有] {table}.{col}")
                continue
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")
            conn.commit()
            print(f"[新增] {table}.{col} {ddl}")
        except sqlite3.Error as e:
            print(f"[失败] {table}.{col} -> {e}")
    conn.close()
    print("迁移完成")


if __name__ == "__main__":
    main()
