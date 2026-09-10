import { useEffect } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import SiteNav from "../components/SiteNav.jsx";
import SiteFooter from "../components/SiteFooter.jsx";
import { findItem, getRelatedItems, getItemsByCat } from "../data/siteData.js";

// 单品详情页：左图右文（用户指定版式）
// URL：/products/:category/:code（如 /products/women/CO-SW001）
export default function ItemDetail() {
  const { category, code } = useParams();
  const found = findItem(category, code);

  useEffect(() => {
    if (found) document.title = `${found.item.name} · ${found.category.label} · FLY`;
  }, [found]);

  if (!found) return <Navigate to="/products" replace />; // 非法品类/款号回产品中心

  const { category: cat, series, item } = found;
  const related = getRelatedItems(cat.key, item.code);
  const more = getItemsByCat(cat.key).length;

  return (
    <>
      <SiteNav />
      <div className="sub-page">
        <div className="wrap id-wrap">
          {/* 面包屑 */}
          <nav className="crumb" aria-label="面包屑" style={{ margin: "30px 0 6px" }}>
            <Link to="/">首页</Link>
            <i className="sep">›</i>
            <Link to="/products">产品</Link>
            <i className="sep">›</i>
            <Link to={`/products/${cat.key}`}>{cat.label}</Link>
            <i className="sep">›</i>
            <em aria-current="page">{item.name}</em>
          </nav>

          {/* 左图右文主体 */}
          <div className="id-grid">
            <div className="id-media">
              <div className="visual">
                {item.hot && <span className="rec">主推</span>}
                <img src={item.img} alt={item.name} />
              </div>
              <span className="id-img-note">单图展示 · 多角度细节图后续补充</span>
            </div>

            <div className="id-info">
              <div className="eyebrow" style={{ marginBottom: 12 }}>
                {cat.label} · {series.name} · {series.season}
              </div>
              <h1 className="id-name">{item.name}</h1>
              <div className="id-code">
                款号 {item.code}
                {item.hot && <span className="tag" style={{ marginLeft: 10 }}>主推</span>}
              </div>

              <p className="id-lead">{item.desc}</p>
              <p className="id-story">{item.story}</p>

              <h2 className="id-h2">设计要点</h2>
              <ul className="id-points">
                {(item.points || []).map((p, i) => <li key={i}>{p}</li>)}
              </ul>

              <div className="id-specs">
                <div className="spec"><dt>面料</dt><dd>{item.fabric}</dd></div>
                <div className="spec"><dt>护理</dt><dd>{item.care}</dd></div>
              </div>

              <div className="id-nav">
                <Link className="btn ghost" to={`/products/${cat.key}`}>← 返回{cat.label}系列</Link>
                <Link className="btn" to="/stores">到店体验 · 查门店</Link>
              </div>
            </div>
          </div>

          {/* 相关推荐：同品类其它款 */}
          {related.length > 0 && (
            <section className="id-related" aria-label="相关款式推荐">
              <div className="sec-head" style={{ marginBottom: 24 }}>
                <div>
                  <div className="eyebrow" style={{ marginBottom: 10 }}>同类推荐</div>
                  <h2 className="sec-title">{cat.label}更多款式</h2>
                  <p className="sec-sub">同系列优先 · 共 {more} 款可浏览</p>
                </div>
              </div>
              <div className="grid list-grid">
                {related.map((r) => (
                  <Link className="p-card" to={`/products/${cat.key}/${r.code}`} key={r.code}>
                    <div className="visual">
                      {r.hot && <span className="rec">主推</span>}
                      <img src={r.img} alt={r.name} loading="lazy" />
                    </div>
                    <div className="cap">
                      <b>{r.name}</b>
                      <span className="meta">{cat.label} · {r.code}</span>
                      <p>{r.desc}</p>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {/* 底部引导 */}
          <div className="cta-line" style={{ paddingBottom: 56 }}>
            <Link className="more" to="/products">← 返回产品中心</Link>
            <Link className="more" to="/products/hot">查看全站主推款式 →</Link>
          </div>
        </div>
      </div>
      <SiteFooter />
    </>
  );
}
