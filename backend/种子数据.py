"""把前台默认新闻（frontend/web/src/data/siteData.js 的 NEWS）灌入 articles 表，作为种子数据。

目的：让「后台 / 首页 / 新闻列表」共享同一份初始内容，消除两套数据源导致的不一致。

用法：
    python 种子数据.py              # 清空 articles 后灌入 9 条（推荐，得到干净初始态）
    python 种子数据.py --append     # 不清空，仅追加库中尚不存在的 slug
    python 种子数据.py --dry-run    # 只预览将写入的内容，不落库

说明：
    - 正文由前端结构化 blogbody（p/h/quote/img）转成 HTML，与前台详情页渲染器（p / h3 / blockquote / figure.art-fig）保持一致。
    - 直接经 ORM 写库，绕过后台接口的富文本净化；生成内容本身安全（全部转义）。
    - 幂等：默认先清空再写入，重复执行结果一致。
"""
from __future__ import annotations

import argparse
import asyncio
import html
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import delete, select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.enums import NewsCategory, Status  # noqa: E402
from app.models.content import Article  # noqa: E402

SITE_DATA = BACKEND_DIR.parent / "frontend" / "web" / "src" / "data" / "siteData.js"

_NODE_CANDIDATES = [
    "node",
    r"C:\Program Files\nodejs\node.exe",
    r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.22.2-2\node.exe",
]

_CAT_MAP = {"company": NewsCategory.COMPANY, "industry": NewsCategory.INDUSTRY}


def find_node() -> str:
    for cand in _NODE_CANDIDATES:
        if cand == "node":
            found = shutil.which("node")
            if found:
                return found
        elif Path(cand).exists():
            return cand
    raise SystemExit(
        "未找到 node，无法从 siteData.js 提取默认新闻。请确认已安装 Node.js 并将其加入 PATH。"
    )


def extract_news() -> list[dict]:
    """用 Node 动态 import siteData.js，导出 NEWS 数组（避免手写重复数据）。"""
    if not SITE_DATA.exists():
        raise SystemExit(f"未找到前端数据文件：{SITE_DATA}")
    node = find_node()
    js = "import(process.env.SITE_DATA_URL).then(m=>process.stdout.write(JSON.stringify(m.NEWS))).catch(e=>{console.error(e);process.exit(1)})"
    env = dict(os.environ, SITE_DATA_URL=SITE_DATA.as_uri())
    res = subprocess.run(
        [node, "--input-type=module", "-e", js],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if res.returncode != 0:
        raise SystemExit("提取默认新闻失败：\n" + (res.stderr or res.stdout or ""))
    return json.loads(res.stdout)


def body_to_html(nodes: list[dict]) -> str:
    """结构化正文 → HTML，标签与前台 NewsDetail 的本地渲染器保持一致。"""
    out: list[str] = []
    for n in nodes or []:
        t = n.get("t")
        if t == "h":
            out.append(f"<h3>{html.escape(n.get('v', ''))}</h3>")
        elif t == "quote":
            out.append(f"<blockquote>{html.escape(n.get('v', ''))}</blockquote>")
        elif t == "img":
            src = html.escape(n.get("src", ""), quote=True)
            cap = n.get("cap", "")
            cap_html = f"<figcaption>{html.escape(cap)}</figcaption>" if cap else ""
            alt = html.escape(cap or "新闻配图", quote=True)
            out.append(
                f'<figure class="art-fig"><img src="{src}" alt="{alt}" loading="lazy" />'
                f"{cap_html}</figure>"
            )
        elif t == "lead":
            out.append(f'<p class="art-lead">{html.escape(n.get("v", ""))}</p>')
        else:  # p 及未知类型按段落处理
            out.append(f"<p>{html.escape(n.get('v', ''))}</p>")
    return "".join(out)


def to_article(n: dict) -> Article:
    date = n.get("date")
    published = datetime.fromisoformat(f"{date}T10:00:00") if date else None
    cat = _CAT_MAP.get(n.get("cat"))
    if cat is None:
        raise SystemExit(f"未知分类：{n.get('cat')}（slug={n.get('slug')}）")
    return Article(
        title=n["title"],
        slug=n["slug"],
        category=cat,
        cover_image=n.get("cover"),
        summary=n.get("lead"),
        content=body_to_html(n.get("body", [])),
        author=n.get("editor"),
        published_at=published,
        status=Status.ONLINE,
    )


async def run(append: bool, dry: bool) -> None:
    news = extract_news()
    print(f"从 siteData.js 读到 {len(news)} 条默认新闻：")
    for n in news:
        print(f"  - [{n.get('cat')}] {n.get('slug')} · {n.get('title')}")

    async with SessionLocal() as db:
        existing: set[str] = set()
        if append:
            existing = set((await db.execute(select(Article.slug))).scalars().all())
        elif not dry:
            # 先清空（务必在 add 之前，否则 autoflush 会先插入再被 DELETE 一起清掉）
            await db.execute(delete(Article))
            print("\n已清空 articles 表。")

        added = 0
        for n in news:
            if append and n["slug"] in existing:
                print(f"  [跳过] slug 已存在：{n['slug']}")
                continue
            art = to_article(n)
            if dry:
                print(f"  [预览] {art.slug} | {art.category.value} | {art.published_at}")
                print(f"         正文片段：{art.content[:60]}…")
            else:
                db.add(art)
            added += 1

        if dry:
            print(f"\n[dry-run] 预计写入 {added} 条，未落库。")
            return

        await db.commit()
        print(f"完成：写入 {added} 条新闻种子数据。")
        total = (await db.execute(select(Article.id))).scalars().all()
        print(f"当前 articles 表共 {len(total)} 条。")


def main() -> None:
    ap = argparse.ArgumentParser(description="把前台默认新闻灌入数据库作为种子数据")
    ap.add_argument("--append", action="store_true", help="不清空，仅追加缺失的 slug")
    ap.add_argument("--dry-run", action="store_true", help="只预览，不落库")
    args = ap.parse_args()
    asyncio.run(run(append=args.append, dry=args.dry_run))


if __name__ == "__main__":
    main()
