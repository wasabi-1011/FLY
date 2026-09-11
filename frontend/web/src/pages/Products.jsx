import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import SiteNav from "../components/SiteNav.jsx";
import SiteFooter from "../components/SiteFooter.jsx";
import PageHero from "../components/PageHero.jsx";
import { CATEGORIES } from "../data/siteData.js";
import { fetchAllItems, localAllItems } from "../data/productsApi.js";

const FILTERS = [
  { key: "all", label: "全部" },
  { key: "women", label: "女装" },
  { key: "men", label: "男装" },
  { key: "kids", label: "童装" },
  { key: "hot", label: "热门" },
];

const EMPTY_STYLE = { textAlign: "center", color: "#8a8a8a", padding: "46px 0", letterSpacing: "0.02em" };

export default function Products() {
  const [filter, setFilter] = useState("all");
  const [all, setAll] = useState(null); // null=加载中；[]=后端暂无在线款式
  const [fallback, setFallback] = useState(false);

  useEffect(() => { document.title = "产品中心 · FLY"; }, []);

  useEffect(() => {
    let alive = true;
    fetchAllItems().then((res) => {
      if (!alive) return;
      if (res.ok) {
        setAll(res.items); // 成功但为空 → 空状态，不回退默认
      } else {
        setAll(localAllItems()); // 仅接口失败才回退本地示例
        setFallback(true);
      }
    });
    return () => { alive = false; };
  }, []);

  const items = all === null
    ? null
    : filter === "all" ? all
      : filter === "hot" ? all.filter((i) => i.hot)
        : all.filter((i) => i.cat === filter);

  return (
    <>
      <SiteNav />
      <div className="sub-page">
        <PageHero
          crumbs={[{ label: "产品" }]}
          title="产品中心"
          en="PRODUCT CENTER"
          sub="男装 · 女装 · 童装 · 当季系列与主推款式"
          bg="/pic/storefront-03.jpg"
        />

        {/* 品类入口条 */}
        <section className="wrap cat-strip" aria-label="按品类浏览">
          {CATEGORIES.map(c => (
            <Link className="cat-card" to={`/products/${c.key}`} key={c.key}>
              <div className="visual"><img src={c.hero} alt={c.label} loading="lazy" />
                <span className="go">进入 {c.label} →</span></div>
              <div className="cap">
                <b>{c.label} <small>{c.en}</small></b>
                <span>{c.slogan}</span>
              </div>
            </Link>
          ))}
        </section>

        {/* 款式罗列（筛选） */}
        <section className="wrap all-list" id="all">
          <div className="sec-head" style={{ marginBottom: 24 }}>
            <div>
              <div className="eyebrow" style={{ marginBottom: 10 }}>当季款式</div>
              <h2 className="sec-title">全系列款式</h2>
            </div>
            <div className="chip-row" role="tablist" aria-label="款式筛选">
              {FILTERS.map(f => (
                <button key={f.key} role="tab" aria-selected={filter === f.key}
                  className={`chip${filter === f.key ? " on" : ""}`} onClick={() => setFilter(f.key)}>
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {fallback && (
            <p style={{ ...EMPTY_STYLE, padding: "18px 0", color: "#b07a2b" }}>
              后端服务暂不可用，以下为本地示例数据
            </p>
          )}
          {items === null && <p style={EMPTY_STYLE}>加载中…</p>}
          {items !== null && items.length === 0 && (
            <p style={EMPTY_STYLE}>
              {filter === "hot" ? "暂无主推款式。" : "暂无上架款式，敬请期待。"}
            </p>
          )}

          <div className="grid list-grid">
            {(items || []).map(it => (
              <Link className="p-card" to={`/products/${it.cat}/${it.code}`} key={it.code}>
                <div className="visual">
                  {it.hot && <span className="rec">主推</span>}
                  <img src={it.img} alt={it.name} loading="lazy" />
                </div>
                <div className="cap">
                  <b>{it.name}</b>
                  <span className="meta">{CATEGORIES.find(c => c.key === it.cat)?.label} · {it.code}</span>
                  <p>{it.desc}</p>
                </div>
              </Link>
            ))}
          </div>
          {filter === "hot" && (
            <div className="cta-line"><span>热门为主推合集，非销量排行。</span>
              <Link className="more" to="/products/hot">进入热门推荐页 →</Link></div>
          )}
        </section>
      </div>
      <SiteFooter />
    </>
  );
}
