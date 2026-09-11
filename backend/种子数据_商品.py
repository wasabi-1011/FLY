# -*- coding: utf-8 -*-
"""把品牌默认商品灌入 items / collections 表，作为款式/系列的种子数据。

目的：让「后台款式管理 / 官网品类页 / 热搜页」共享同一份初始商品，消除两套数据源。
     图片为 AI 生成并已落到 `frontend/web/public/pic/`（前台以 /pic/xxx 访问），
     原始 PNG 保留在 `D:\\FLY网站\\picTest\\`。

层级（v2.2 起）：品类（款式自带）→ 款式 → 系列（挂在款式下，选填 0..n）。

本期数据规模（v2.4 调整）：**5 件款式 + 8 个系列**
    品类         款号        款式        系列数   系列
    women       CO-SW001   牛仔裤       2       牛仔裤系列1 / 牛仔裤系列2
    men         CO-MN001   工装夹克     3       工装夹克系列1 / 系列2 / 系列3
    women       CO-SW002   针织连衣裙   1       针织连衣裙系列1
    men         CO-MN002   短袖T恤      1       短袖T恤系列1
    kids        CO-KD001   卫衣         1       卫衣系列1

用法：
    python 种子数据_商品.py             # 清空 items/collections 后灌入 5 件款式 + 8 个系列
    python 种子数据_商品.py --dry-run   # 只预览，不落库
    python 种子数据_商品.py --append    # 不清空，仅补库中尚不存在的款号

幂等：默认先清空再写入，重复执行结果一致。
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import delete, select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.enums import Category, Season, Status  # noqa: E402
from app.models.product import Collection, Item  # noqa: E402

# 5 件款式；`pic` = /pic/<pic>.jpg，`series` = [(系列名, 系列封面 pic), ...]
# hot_order 决定热门页顺序（与前台 HOT_ORDER 一致）。
ITEMS: list[dict] = [
    dict(item_code="CO-SW001", name="牛仔裤", category="women", pic="item-jeans", hot_order=1,
         desc="高腰直筒版型，原色丹宁挺括有型，久穿不易变形。",
         fabric="12oz 原色纯棉丹宁（示例文案）", fit="高腰直筒，微弹",
         series=[("牛仔裤系列1", "series-jeans-1"), ("牛仔裤系列2", "series-jeans-2")]),

    dict(item_code="CO-MN001", name="工装夹克", category="men", pic="item-jacket", hot_order=2,
         desc="多袋工装结构 + 耐磨棉感面料，通勤与户外一件搞定。",
         fabric="厚磅磨毛棉质斜纹（示例文案）", fit="宽松直筒，立领",
         series=[("工装夹克系列1", "series-jacket-1"),
                 ("工装夹克系列2", "series-jacket-2"),
                 ("工装夹克系列3", "series-jacket-3")]),

    dict(item_code="CO-SW002", name="针织连衣裙", category="women", pic="item-dress", hot_order=3,
         desc="米白中长款针织裙，收腰垂坠，单穿即是一整身造型。",
         fabric="羊毛混纺细针织（示例文案）", fit="收腰中长款",
         series=[("针织连衣裙系列1", "series-dress-1")]),

    dict(item_code="CO-MN002", name="短袖T恤", category="men", pic="item-tee", hot_order=4,
         desc="挺括纯棉基础款，领口不易外翻，叠穿单穿都成立。",
         fabric="32 支精梳纯棉（示例文案）", fit="合体直筒",
         series=[("短袖T恤系列1", "series-tee-1")]),

    dict(item_code="CO-KD001", name="卫衣", category="kids", pic="item-hoodie", hot_order=5,
         desc="软糯亲肤棉，连帽宽松版型，奔跑攀爬都不受束缚。",
         fabric="A 类亲肤棉抓绒（示例文案）", fit="宽松落肩，连帽",
         series=[("卫衣系列1", "series-hoodie-1")]),
]

CAT_LABEL = {"women": "女装", "men": "男装", "kids": "童装"}


def to_item(spec: dict) -> Item:
    cat = spec["category"]
    return Item(
        item_code=spec["item_code"],
        name=spec["name"],
        category=Category(cat),
        is_hot=True,                      # 与前台本地数据一致：这几件都是运营主推
        hot_sort=spec["hot_order"],
        images=[f"/pic/{spec['pic']}.jpg"],
        fabric=spec.get("fabric"),
        fit_description=spec.get("fit"),
        description=spec.get("desc"),
        sort_weight=max(0, 100 - spec["hot_order"]),
        status=Status.ONLINE,
    )


def to_series(item_id: int, name: str, cover_pic: str) -> Collection:
    return Collection(
        item_id=item_id,
        name=name,
        year=2026,
        season=Season.AUTUMN_WINTER,
        cover_image=f"/pic/{cover_pic}.jpg",
        status=Status.ONLINE,
    )


async def run(dry: bool, append: bool) -> None:
    total_series = sum(len(s["series"]) for s in ITEMS)
    print(f"准备写入 {len(ITEMS)} 件款式 / {total_series} 个系列（图片取自 /pic/<name>.jpg）：")
    for s in ITEMS:
        names = "、".join(n for n, _ in s["series"]) or "（无系列）"
        print(f"  - [{CAT_LABEL[s['category']]}] {s['item_code']} {s['name']} · 系列「{names}」")

    if dry:
        print("\n[dry-run] 未落库。")
        return

    async with SessionLocal() as db:
        existing: set[str] = set()
        if append:
            existing = set((await db.execute(select(Item.item_code))).scalars().all())
        else:
            # 先清空（先删系列再删款式，避免外键顺序问题）
            await db.execute(delete(Collection))
            await db.execute(delete(Item))
            print("\n已清空 items / collections 表。")

        added_item = added_series = 0
        for spec in ITEMS:
            if append and spec["item_code"] in existing:
                print(f"  [跳过] 款号已存在：{spec['item_code']}")
                continue
            it = to_item(spec)
            db.add(it)
            await db.flush()  # 取到 it.id
            added_item += 1
            for sname, spic in spec["series"]:
                db.add(to_series(it.id, sname, spic))
                added_series += 1

        await db.commit()
        print(f"完成：写入 {added_item} 件款式 / {added_series} 个系列。")
        total_i = len((await db.execute(select(Item.id))).scalars().all())
        total_c = len((await db.execute(select(Collection.id))).scalars().all())
        print(f"当前 items 共 {total_i} 条，collections 共 {total_c} 条。")


def main() -> None:
    ap = argparse.ArgumentParser(description="把品牌默认商品灌入数据库作为种子数据")
    ap.add_argument("--dry-run", action="store_true", help="只预览，不落库")
    ap.add_argument("--append", action="store_true", help="不清空，仅追加缺失的款号")
    args = ap.parse_args()
    asyncio.run(run(dry=args.dry_run, append=args.append))


if __name__ == "__main__":
    main()
