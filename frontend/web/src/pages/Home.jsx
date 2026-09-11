import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import SiteNav from "../components/SiteNav.jsx";
import SiteFooter from "../components/SiteFooter.jsx";
import Hero from "../components/Hero.jsx";
import StoreEntry from "../components/StoreEntry.jsx";
import { CATEGORIES, HOME_COLLECTIONS, collectionsFromItems, getHotItems } from "../data/siteData.js";
import { fetchLatestNews, localLatest } from "../data/newsApi.js";
import { fetchHotItems, fetchAllItems } from "../data/productsApi.js";

const HOT_META = (list, code) => {
  const it = list.find(h => h.code === code);
  const c = it && CATEGORIES.find(x => x.key === it.cat);
  return `${c ? c.label : ""} · ${code}`;
};

const QUICK = [
  { b: "产品", s: "品类 · 系列 · 款式", to: "/products", icon: <><path d="M3 5h18l-1 14H4z" /><path d="M8 9v6M16 9v6" /></> },
  { b: "门店", s: "地图 · 城市筛选", to: "/stores", icon: <><path d="M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11Z" /><circle cx="12" cy="10" r="2.5" /></> },
  { b: "新闻", s: "企业 · 行业资讯", to: "/news/company", icon: <><path d="M4 5h16v14H4z" /><path d="M8 8h8M8 12h8M8 16h5" /></> },
  { b: "招聘", s: "社招 · 校招", soon: true, icon: <><path d="M8 21a4 4 0 0 1 8 0" /><circle cx="12" cy="7" r="4" /></> },
  { b: "关于我们", s: "品牌 · 历程 · 联系", to: "/about", icon: <><circle cx="12" cy="7" r="3.5" /><path d="M5 21a7 7 0 0 1 14 0" /></> },
];

export default function Home() {
  const hotRef = useRef(null);
  // 首页新闻与 /news 同源：都读数据库；接口不可用才回退本地默认
  const [news, setNews] = useState(null); // null = 加载中
  const [newsFallback, setNewsFallback] = useState(false);
  // 首页「当季系列」「热门推荐」同样以数据库为准：先用本地兜底渲染，接口回来再替换
  // （约定同 newsApi：接口成功但为空 → 显示空状态；仅接口失败 → 保留本地兜底）
  const [hot, setHot] = useState(() => getHotItems());
  const [cols, setColls] = useState(HOME_COLLECTIONS);

  useEffect(() => {
    let alive = true;
    fetchLatestNews(3).then((res) => {
      if (!alive) return;
      if (res.ok) setNews(res.items);
      else { setNews(localLatest(3)); setNewsFallback(true); }
    });
    return () => { alive = false; };
  }, []);

  // 款式 / 系列：与产品中心同源（GET /api/products/hot、/api/products/{category}）
  useEffect(() => {
    let alive = true;
    fetchHotItems().then((res) => {
      if (!alive || !res.ok) return;   // 失败 → 保留本地兜底
      setHot(res.items);               // 成功（含空数组）→ 以服务端为准
    });
    fetchAllItems().then((res) => {
      if (!alive || !res.ok) return;
      setColls(collectionsFromItems(res.items));
    });
    return () => { alive = false; };
  }, []);

  // 热门推荐入场动效（进入视口时逐个加 .in）；数据异步到达后需重跑，否则卡片停在 opacity:0
  useEffect(() => {
    const el = hotRef.current;
    if (!el) return;
    const cards = el.querySelectorAll(".hot-card");
    if (!cards.length) return;
    if (!("IntersectionObserver" in window)) {
      cards.forEach(c => c.classList.add("in"));
      return;
    }
    const obs = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        cards.forEach((c, i) => setTimeout(() => c.classList.add("in"), i * 60));
        obs.disconnect();
      }
    }, { threshold: 0.2 });
    obs.observe(el);
    return () => obs.disconnect();
  }, [hot]);

  return (
    <>
      <SiteNav />

      <Hero />

      {/* 2. 品牌主张 */}
      <section className="manifesto" id="brand-story">
        <div className="wrap">
          <div className="quote">
            <div className="eyebrow" style={{ marginBottom: 20 }}>品牌主张</div>
            <p>「穿出自我，随心而飞」——<br />我们不定义风格，只提供让每个人找到自己的可能。</p>
            <div className="sign">— FLY 品牌价值主张 · 中英混排 · 一句话贯穿全站 —</div>
          </div>
          <div className="img-band"><img src="/pic/brand.jpg" alt="FLY 品牌主张配图" /></div>
        </div>
      </section>

      {/* 3. 当季系列推荐 */}
      <section id="products">
        <div className="wrap">
          <div className="sec-head">
            <div>
              <div className="eyebrow" style={{ marginBottom: 12 }}>本季系列</div>
              <h2 className="sec-title">当季系列推荐</h2>
              <p className="sec-sub">以系列与大片呈现，弱化货架感（PRD 6.3 定位）。点击进入品类。</p>
            </div>
            <Link className="more" to="/products">进入产品中心 →</Link>
          </div>
          <div className="coll-grid">
            {cols.map((c, i) => (
              <Link className="coll-card" to={`/products/${c.cat}`} key={i}>
                <div className="visual"><img src={c.img} alt={c.title} loading="lazy" /><span className="tag">{c.tag}</span></div>
                <div className="cap"><h3>{c.title}</h3><p>{c.desc}</p></div>
              </Link>
            ))}
            {cols.length === 0 && (
              <p className="sec-sub">暂无上架系列（可在后台「款式列表 / 系列管理」维护）。</p>
            )}
          </div>
        </div>
      </section>

      {/* 4. 热门推荐 */}
      <div className="hot-band" id="hot" ref={hotRef}>
        <div className="wrap">
          <div className="sec-head">
            <div>
              <div className="eyebrow" style={{ marginBottom: 12, color: "#a89477" }}>主推单品 · 人工打标</div>
              <h2 className="sec-title">热门推荐</h2>
              <p className="sec-sub" style={{ color: "#b3a99a" }}>运营人工标记的当季主推款式（非销量排行，PRD N12 红线）。</p>
            </div>
            <Link className="more" to="/products/hot" style={{ color: "#a89477" }}>查看全部 →</Link>
          </div>
          <div className="hot-grid">
            {hot.map((h, i) => (
              <Link className="hot-card" to={`/products/${h.cat}/${h.code}`} key={i}>
                <div className="visual"><span className="rec">推荐</span><img src={h.img} alt={h.name} loading="lazy" /></div>
                <div className="cap"><b>{h.name}</b><span>{HOT_META(hot, h.code)}</span></div>
              </Link>
            ))}
            {hot.length === 0 && (
              <p className="sec-sub" style={{ color: "#b3a99a" }}>暂无主推款式（可在后台「款式列表」标记热门）。</p>
            )}
          </div>
        </div>
      </div>

      {/* 5. 门店入口 */}
      <StoreEntry />

      {/* 6. 新闻推荐 */}
      <section id="news">
        <div className="wrap">
          <div className="sec-head">
            <div>
              <div className="eyebrow" style={{ marginBottom: 12 }}>新闻</div>
              <h2 className="sec-title">品牌动态</h2>
              <p className="sec-sub">企业新闻 · 行业资讯（PRD F5）。</p>
            </div>
            <Link className="more" to="/news/company">全部新闻 →</Link>
          </div>
          {newsFallback && (
            <p className="news-note" style={{ marginTop: 12 }}>后端暂不可用，当前展示本地默认内容</p>
          )}
          {news === null ? (
            <p className="news-empty">加载中…</p>
          ) : news.length === 0 ? (
            <p className="news-empty">暂无新闻内容</p>
          ) : (
            <div className="news-grid">
              {news.map((n, i) => (
                <Link className="news-card" to={`/news/${n.cat}/${n.slug}`} key={n.slug || i}>
                  <div className="thumb"><img src={n.cover} alt={n.title} loading="lazy" /></div>
                  <div className="cat">{n.cat === "company" ? "企业新闻" : "行业资讯"}</div>
                  <h3>{n.title}</h3>
                  <div className="meta">{n.date}{n.place ? ` · ${n.place}` : ""}</div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* 7. 五大栏目快捷入口 */}
      <section className="quick-panel" id="sections">
        <div className="wrap">
          <div className="sec-head" style={{ marginBottom: 28 }}>
            <div><div className="eyebrow" style={{ marginBottom: 12 }}>全站栏目</div><h2 className="sec-title">五大栏目</h2></div>
          </div>
          <div className="quick-grid">
            {QUICK.map((q, i) => q.soon ? (
              <div className="quick-item soon" key={i} title="建设中">
                <svg viewBox="0 0 24 24">{q.icon}</svg>
                <b>{q.b}<i className="soon-tag">建设中</i></b><span>{q.s}</span>
              </div>
            ) : (
              <Link className="quick-item" to={q.to} key={i}>
                <svg viewBox="0 0 24 24">{q.icon}</svg>
                <b>{q.b}</b><span>{q.s}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <SiteFooter />
    </>
  );
}
