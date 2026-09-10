import { useEffect } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import SiteNav from "../components/SiteNav.jsx";
import SiteFooter from "../components/SiteFooter.jsx";
import PageHero from "../components/PageHero.jsx";
import { getCategory, getSeriesByCat } from "../data/siteData.js";

export default function CategoryPage() {
  const { category } = useParams();
  const cat = getCategory(category);

  useEffect(() => {
    if (cat) document.title = `${cat.label} · FLY`;
  }, [cat]);

  if (!cat) return <Navigate to="/products" replace />; // 非法品类回聚合页

  const series = getSeriesByCat(cat.key);

  return (
    <>
      <SiteNav />
      <div className="sub-page">
        <PageHero
          crumbs={[{ label: "产品", to: "/products" }, { label: cat.label }]}
          title={cat.label}
          en={cat.en}
          sub={cat.slogan}
          bg={cat.hero}
        />

        {/* 系列区块 */}
        <section className="wrap">
          {series.map(s => (
            <div className="ser-block" key={s.name}>
              <div className="ser-head">
                <div>
                  <div className="eyebrow" style={{ marginBottom: 10 }}>{s.season} · {s.en}</div>
                  <h2 className="sec-title">{s.name}</h2>
                </div>
                <span className="count-chip">{s.items.length} 款</span>
              </div>
              <p className="ser-desc">{s.desc}</p>
              <div className="grid list-grid">
                {s.items.map(it => (
                  <Link className="p-card" to={`/products/${cat.key}/${it.code}`} key={it.code}>
                    <div className="visual">
                      {it.hot && <span className="rec">主推</span>}
                      <img src={it.img} alt={it.name} loading="lazy" />
                    </div>
                    <div className="cap">
                      <b>{it.name}</b>
                      <span className="meta">{cat.label} · {it.code}</span>
                      <p>{it.desc}</p>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </section>

        {/* 底部引导 */}
        <section className="wrap">
          <div className="cta-line">
            <Link className="more" to="/products">← 返回产品中心</Link>
            <Link className="more" to="/products/hot">查看全站主推款式 →</Link>
          </div>
        </section>
      </div>
      <SiteFooter />
    </>
  );
}
