"""种子数据：灌入示例内容，便于本地直接启动验证。

运行：python -m app.seed
说明：门店坐标为占位近似 GCJ-02 坐标，上线前须由零售运营替换为实测坐标（FR-F45）。
"""
from __future__ import annotations

import asyncio
from datetime import datetime

from sqlalchemy import select

from app.database import SessionLocal, init_db
from app.enums import (
    BlockType,
    Category,
    CoopType,
    NewsCategory,
    Role,
    Season,
    Status,
    StoreType,
)
from app.models.admin import AdminUser
from app.models.content import Article, Block, Page, PageVersion
from app.models.contact import ContactMessage
from app.models.product import Collection, Item
from app.models.store import Store, StoreStock
from app.security import hash_password


STORE_SEED = [
    ("广州天河城旗舰店", "广东", "广州", "天河区", "天河路 208 号", StoreType.FLAGSHIP, 113.3245, 23.1356),
    ("广州正佳广场店", "广东", "广州", "天河区", "天河路 228 号", StoreType.STANDARD, 113.3301, 23.1378),
    ("广州天环广场店", "广东", "广州", "天河区", "天河路 218 号", StoreType.STANDARD, 113.3278, 23.1365),
    ("武汉国际广场店", "湖北", "武汉", "江汉区", "解放大道 690 号", StoreType.STANDARD, 114.2734, 30.5951),
    ("武汉楚河汉街店", "湖北", "武汉", "武昌区", "中北路 171 号", StoreType.STANDARD, 114.3412, 30.5678),
    ("武汉光谷广场店", "湖北", "武汉", "洪山区", "珞喻路 678 号", StoreType.STANDARD, 114.4056, 30.5067),
    ("深圳万象天地旗舰店", "广东", "深圳", "南山区", "深南大道 9668 号", StoreType.FLAGSHIP, 113.9352, 22.5406),
    ("深圳海岸城店", "广东", "深圳", "南山区", "文心五路 33 号", StoreType.STANDARD, 113.9256, 22.5201),
    ("深圳万象城店", "广东", "深圳", "罗湖区", "宝安南路 1881 号", StoreType.STANDARD, 114.1234, 22.5467),
    ("上海兴业太古汇店", "上海", "上海", "静安区", "南京西路 789 号", StoreType.STANDARD, 121.4512, 31.2234),
    ("上海环贸 iapm 店", "上海", "上海", "徐汇区", "淮海中路 999 号", StoreType.STANDARD, 121.4678, 31.2134),
    ("上海静安嘉里中心店", "上海", "上海", "静安区", "南京西路 1515 号", StoreType.STANDARD, 121.4456, 31.2234),
    ("北京三里屯太古里旗舰店", "北京", "北京", "朝阳区", "三里屯路 19 号", StoreType.FLAGSHIP, 116.4534, 39.9367),
    ("北京 SKP 店", "北京", "北京", "朝阳区", "建国路 87 号", StoreType.STANDARD, 116.4623, 39.9156),
    ("北京国贸店", "北京", "北京", "朝阳区", "建国门外大街 1 号", StoreType.STANDARD, 116.4601, 39.9089),
    ("成都太古里店", "四川", "成都", "锦江区", "中纱帽街 8 号", StoreType.STANDARD, 104.0856, 30.6543),
    ("成都 IFS 店", "四川", "成都", "锦江区", "红星路三段 1 号", StoreType.STANDARD, 104.0798, 30.6598),
    ("成都万象城店", "四川", "成都", "成华区", "双庆路 8 号", StoreType.STANDARD, 104.1023, 30.6601),
    ("杭州湖滨银泰店", "浙江", "杭州", "上城区", "延安路 530 号", StoreType.STANDARD, 120.1678, 30.2543),
    ("西安大悦城店", "陕西", "西安", "雁塔区", "慈恩西路 66 号", StoreType.STANDARD, 108.9612, 34.2234),
]


async def _create_page(db, slug, title, page_type, blocks, publish, created_by):
    page = Page(slug=slug, title=title, page_type=page_type, status=Status.DRAFT)
    db.add(page)
    await db.flush()
    version = PageVersion(page_id=page.id, version_no=1, created_by=created_by, note="初始版本")
    db.add(version)
    await db.flush()
    for i, b in enumerate(blocks):
        db.add(
            Block(
                page_version_id=version.id,
                type=BlockType(b["type"]),
                config_json=b["config_json"],
                sort=i,
                mobile_visible=b.get("mobile_visible", True),
            )
        )
    if publish:
        page.current_version_id = version.id
        page.status = "published"
    await db.flush()
    return page


async def seed_data() -> None:
    await init_db()
    async with SessionLocal() as db:
        # 幂等：已存在 admin 则跳过
        if (
            await db.execute(select(AdminUser).where(AdminUser.username == "admin"))
        ).scalar_one_or_none():
            print("已检测到种子数据，跳过。")
            return

        # ---- 后台账号 ----
        db.add_all(
            [
                AdminUser(username="admin", password_hash=hash_password("admin1234"),
                          role=Role.SUPER_ADMIN),
                AdminUser(username="editor", password_hash=hash_password("editor1234"),
                          role=Role.CONTENT_OPS),
                AdminUser(username="merch", password_hash=hash_password("merch1234"),
                          role=Role.MERCH_STORE_OPS),
            ]
        )
        await db.flush()
        super_id = (
            await db.execute(select(AdminUser.id).where(AdminUser.username == "admin"))
        ).scalar()

        # ---- 门店 ----
        stores = []
        for name, prov, city, dist, addr, stype, lng, lat in STORE_SEED:
            s = Store(
                name=name, province=prov, city=city, district=dist, address=addr,
                lng=lng, lat=lat, store_type=stype, status=Status.ONLINE,
                business_hours="10:00-22:00", phone="400-000-0000",
            )
            db.add(s)
            stores.append(s)
        await db.flush()

        # ---- 系列 + 款式 ----
        def make_items(col_id, prefix, n, hot_count):
            items = []
            for i in range(1, n + 1):
                is_hot = i <= hot_count
                it = Item(
                    item_code=f"FLY26AW-{prefix}{i:03d}",
                    name=f"{prefix} 单品 {i}",
                    collection_id=col_id,
                    is_hot=is_hot,
                    hot_sort=i if is_hot else 0,
                    images=[f"https://cdn.example.com/{prefix}-{i}-1.jpg"],
                    fabric="聚酯纤维 100%",
                    colors=[{"name": "雾灰", "hex": "#9aa0a6"}, {"name": "墨黑", "hex": "#1a1a1a"}],
                    fit_description="宽松版型",
                    sort_weight=n - i,
                    status=Status.ONLINE,
                )
                db.add(it)
                items.append(it)
            return items

        collections_spec = [
            ("men", "2026 秋冬·城野机能", "AUTUMN_WINTER", 2026, 6, 3),
            ("women", "2026 秋冬·柔光系列", "AUTUMN_WINTER", 2026, 6, 3),
            ("kids", "2026 秋冬·童趣暖冬", "AUTUMN_WINTER", 2026, 4, 2),
        ]
        item_codes = []
        for cat, name, season, year, n, hot in collections_spec:
            col = Collection(
                name=name, slug=f"2026aw-{cat}-demo", subtitle=f"{cat} 示例系列",
                category=Category(cat), year=year, season=Season[season],
                cover_image=f"https://cdn.example.com/{cat}-cover.jpg",
                status=Status.ONLINE, published_at=datetime.utcnow(),
            )
            db.add(col)
            await db.flush()
            its = make_items(col.id, cat[:3].upper(), n, hot)
            item_codes += [it.item_code for it in its]

        # ---- 门店库存（内部） ----
        for s in stores[:6]:
            for code in item_codes[:3]:
                db.add(StoreStock(store_id=s.id, item_code=code, quantity=8))

        # ---- 新闻 ----
        db.add_all(
            [
                Article(title="FLY 2026 秋冬系列发布", slug="2026aw-launch",
                        category=NewsCategory.COMPANY, status=Status.ONLINE,
                        summary="城野机能主题全新登场", author="品牌市场部",
                        cover_image="https://cdn.example.com/news-1.jpg",
                        content="<p>FLY 2026 秋冬系列正式发布……</p>",
                        published_at=datetime.utcnow()),
                Article(title="2026 秋冬面料趋势观察", slug="fabric-trend-2026",
                        category=NewsCategory.INDUSTRY, status=Status.ONLINE,
                        summary="可持续面料成为主流", author="内容运营",
                        cover_image="https://cdn.example.com/news-2.jpg",
                        content="<p>本季面料趋势……</p>",
                        published_at=datetime.utcnow()),
            ]
        )

        # ---- 固定页（关于我们 / 招聘） ----
        about_blocks = [
            {"type": "RICH_TEXT", "config_json": {"html": "<h2>关于 FLY</h2><p>穿出自我，随心而飞。</p>"}},
        ]
        for slug, title in [
            ("about/fly", "关于 FLY"), ("about/brand", "品牌介绍"),
            ("about/history", "发展历程"), ("about/contact", "联系我们"),
            ("join/social", "社会招聘"), ("join/campus", "校园招聘"),
        ]:
            await _create_page(db, slug, title, "fixed", about_blocks, publish=True, created_by=super_id)

        # 联系页补一条留言
        db.add(ContactMessage(name="张三", company="某媒体", contact_type="email",
                              contact="zhangsan@example.com", coop_type=CoopType.MEDIA,
                              content="希望采访品牌负责人。"))

        # ---- 首页（CMS 11 区块示例） ----
        home_blocks = [
            {"type": "FULLSCREEN_VISUAL", "config_json": {
                "autoplay": 5,
                "frames": [
                    {"image": "https://cdn.example.com/home-frame-1.jpg",
                     "layers": [
                         {"text": "FLY", "style": "brand-wordmark"},
                         {"text": "FEEL · LIVE · YOURSELF", "style": "en-sub"},
                         {"text": "穿出自我，随心而飞", "style": "cn-sub"}],
                     "active": True},
                    {"image": "https://cdn.example.com/home-frame-2.jpg",
                     "layers": [{"text": "2026 秋冬·城野机能", "style": "collection"}],
                     "active": True},
                ],
            }},
            {"type": "IMAGE_BANNER", "config_json": {"image": "https://cdn.example.com/banner.jpg", "link": "/products/men"}},
            {"type": "COLLECTION_RECOMMEND", "config_json": {"title": "当季系列"}},
            {"type": "HOT_RECOMMEND", "config_json": {"title": "热门推荐", "count": 8}},
            {"type": "STORE_ENTRY", "config_json": {"title": "寻找门店", "cities_count": 8, "stores_count": 20}},
            {"type": "NEWS_RECOMMEND", "config_json": {"title": "品牌动态"}},
            {"type": "COLUMN_ENTRY", "config_json": {"title": "快速导航"}},
        ]
        await _create_page(db, "home", "首页", "fixed", home_blocks, publish=True, created_by=super_id)

        await db.commit()
        print("种子数据写入完成。")


if __name__ == "__main__":
    asyncio.run(seed_data())
