import { useEffect } from "react";
import { Link } from "react-router-dom";
import SiteNav from "../components/SiteNav.jsx";
import SiteFooter from "../components/SiteFooter.jsx";
import PageHero from "../components/PageHero.jsx";
import { CATEGORIES, getHotItems } from "../data/siteData.js";

export default function HotPage() {
  const hot = getHotItems();
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
          <div className="hot-grid">
            {hot.map(it => (
              <Link className="hot-card in" to={`/products/${it.cat}/${it.code}`} key={it.code}>
                <div className="visual"><span className="rec">推荐</span><img src={it.img} alt={it.name} loading="lazy" /></div>
                <div className="cap">
                  <b>{it.name}</b>
                  <span>{CATEGORIES.find(c => c.key === it.cat)?.label} · {it.code}</span>
                  <p className="hot-desc">{it.desc}</p>
                </div>
              </Link>
            ))}
          </div>

          {/* 品类快捷 */}
          <div className="hot-cats">
            {CATEGORIES.map(c => (
              <Link className="btn ghost" to={`/products/${c.key}`} key={c.key}>{c.label}系列 →</Link>
            ))}
          </div>
        </div>
      </div>

      <SiteFooter />
    </>
  );
}
