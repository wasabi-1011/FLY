"""查看「首页轮播图」在数据库中的实际存储位置与内容。

用法（在 backend 目录下）：
    .venv\\Scripts\\python.exe 查看首页轮播.py
    .venv\\Scripts\\python.exe 查看首页轮播.py --all      # 额外列出所有历史版本

存储链路：
    pages(slug='home').current_version_id
      -> page_versions(id=...)           # 每次后台保存都会新建并发布一个版本
        -> blocks(type='FULLSCREEN_VISUAL').config_json.frames   # 轮播帧数组
图片本体不入库，只存路径字符串 /uploads/xxx.jpg，文件在 backend/uploads/ 目录。
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fly.db")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")


def main() -> None:
    show_all = "--all" in sys.argv
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    page = cur.execute(
        "SELECT * FROM pages WHERE slug='home'"
    ).fetchone()
    if not page:
        print("未找到 slug='home' 的页面，请先执行： python -m app.seed")
        return

    print("=" * 68)
    print("① pages 表（页面主记录）")
    print(f"   id={page['id']}  slug={page['slug']}  标题={page['title']}")
    print(f"   status={page['status']}  current_version_id={page['current_version_id']}")
    print(f"   updated_at={page['updated_at']}")

    vid = page["current_version_id"]
    ver = cur.execute("SELECT * FROM page_versions WHERE id=?", (vid,)).fetchone()
    if not ver:
        print("当前版本不存在")
        return

    print()
    print("② page_versions 表（当前生效版本）")
    print(f"   id={ver['id']}  version_no={ver['version_no']}  note={ver['note']}")
    print(f"   created_at={ver['created_at']}  created_by={ver['created_by']}")

    blocks = cur.execute(
        "SELECT * FROM blocks WHERE page_version_id=? ORDER BY sort", (ver["id"],)
    ).fetchall()
    hero = next((b for b in blocks if str(b["type"]).upper() == "FULLSCREEN_VISUAL"), None)

    print()
    print("③ blocks 表（该版本的区块）")
    for b in blocks:
        mark = "  <<< 首页轮播就在这里" if hero and b["id"] == hero["id"] else ""
        print(f"   id={b['id']}  type={b['type']}  sort={b['sort']}{mark}")

    if not hero:
        print("   未找到 FULLSCREEN_VISUAL 区块")
        return

    cfg = json.loads(hero["config_json"] or "{}")
    frames = cfg.get("frames") or []
    print()
    print(f"④ block id={hero['id']} 的 config_json.frames（共 {len(frames)} 帧）")
    print(f"   autoplay = {cfg.get('autoplay')} 秒")
    for i, f in enumerate(frames, 1):
        img = f.get("image") or ""
        active = f.get("active", True)
        exists = ""
        if img.startswith("/uploads/"):
            p = os.path.join(UPLOAD_DIR, os.path.basename(img))
            exists = "  [文件存在]" if os.path.exists(p) else "  [!! 文件缺失]"
        elif img:
            exists = "  [外链]"
        print(f"   帧{i}  {'显示中' if active else '隐藏  '}  标题={f.get('title','')!r}")
        print(f"        副标题={f.get('sub','')!r}  链接={f.get('link','')!r}")
        print(f"        图片={img}{exists}")

    if show_all:
        print()
        print("⑤ home 页所有历史版本（可回滚）")
        for v in cur.execute(
            "SELECT * FROM page_versions WHERE page_id=? ORDER BY version_no",
            (page["id"],),
        ):
            mark = "  <<< 当前生效" if v["id"] == vid else ""
            print(f"   version_no={v['version_no']}  id={v['id']}  {v['created_at']}  {v['note']}{mark}")

    print()
    print("=" * 68)
    print("提示：后台每次保存都会新建版本并立即发布，所以 blocks 里会有多份旧数据，")
    print("      只有 current_version_id 指向的那个版本的内容会显示在前台。")
    print("      用数据库工具查看时若没变化，请刷新（F5 / 重新执行查询）。")


if __name__ == "__main__":
    main()
