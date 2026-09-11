import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import SiteNav from "../components/SiteNav.jsx";
import SiteFooter from "../components/SiteFooter.jsx";
import PageHero from "../components/PageHero.jsx";
import { CATEGORIES } from "../data/siteData.js";
import { fetchHotItems, localHotItems } from "../data/productsApi.js";

const EMPTY_STYLE = { textAlign: "center", color: "#cfd3dc", padding: "40px 0", letterSpacing: "0.02em" };

export default function HotPage() {
  const [hot, setHot] = useState(null); // null=加载中；[]=后端暂无主推
  const [fallback, setFallback] = useState(false);

  useEffect(() => {
    let alive = true;
    fetchHotItems().then((res) => {
      if (!alive) return;
      if (res.ok) {
        setHot(res.items); // 成功但为空 → 空状态，不回退默认
      } else {
        setHot(localHotItems()); // 仅接口失败才回退本地示例
        setFallback(true);
      }
    });
    return () => { alive = false; };
  }, []);

  useEffect(() => { document.title = "热门推荐 · FLY"; }, []);

  return (
    <>
      <SiteNav />
      <div className="sub-page">
        <PageHero dark
          crumbs={[{ label: "产品", to: "/products" }, { label: "热门推荐" }]}
          title="热门推荐"
          en="HOT PICKS"
          sub="运营人工标记的当季主推 · 非销量排行"
        />
      </div>

      {/* 深色热门区（延续首页 hot-band 质感） */}
      <div className="hot-band hot-page">
        <div className="wrap">
          {fallback && (
            <p style={{ ...EMPTY_STYLE, color: "#e0b15c" }}>后端服务暂不可用，以下为本地示例数据</p>
          )}
          {hot === null && <p style={EMPTY_STYLE}>加载中…</p>}
          {hot !== null && hot.length === 0 && (
            <p style={EMPTY_STYLE}>暂无主推款式，运营在后台「款式列表」勾选热门后会出现在这里。</p>
          )}

          <div className="hot-grid">
            {(hot || []).map((it) => (
              <Link className="hot-card in" to={`/products/${it.cat}/${it.code}`} key={it.code}>
                <div className="visual"><span className="rec">推荐</span><img src={it.img} alt={it.name} loading="lazy" /></div>
                <div className="cap">
                  <b>{it.name}</b>
                  <span>{CATEGORIES.find((c) => c.key === it.cat)?.label} · {it.code}</span>
                  <p className="hot-desc">{it.desc}</p>
                </div>
              </Link>
            ))}
          </div>

          {/* 品类快捷 */}
          <div className="hot-cats">
            {CATEGORIES.map((c) => (
              <Link className="btn ghost" to={`/products/${c.key}`} key={c.key}>{c.label}系列 →</Link>
            ))}
          </div>
        </div>
      </div>

      <SiteFooter />
    </>
  );
}
