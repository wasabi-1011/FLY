import { useEffect, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import SiteNav from "../components/SiteNav.jsx";
import SiteFooter from "../components/SiteFooter.jsx";
import PageHero from "../components/PageHero.jsx";
import { getCategory } from "../data/siteData.js";
import { fetchCategoryPage, localItemsByCat } from "../data/productsApi.js";

const EMPTY_STYLE = { textAlign: "center", color: "#8a8a8a", padding: "46px 0", letterSpacing: "0.02em" };

export default function CategoryPage() {
  const { category } = useParams();
  const cat = getCategory(category);
  const catKey = cat ? cat.key : null;
  // items: null = 加载中；[] = 后端确认该品类暂无上架款式（显示空状态）
  const [items, setItems] = useState(null);
  const [fallback, setFallback] = useState(false);

  useEffect(() => {
    if (!catKey) return;
    let alive = true;
    setItems(null);
    setFallback(false);
    fetchCategoryPage(catKey).then((res) => {
      if (!alive) return;
      if (res.ok) {
        setItems(res.items); // 成功但为空 → 空状态，不回退默认
      } else {
        setItems(localItemsByCat(catKey)); // 仅接口失败才回退本地示例
        setFallback(true);
      }
    });
    return () => { alive = false; };
  }, [catKey]);

  useEffect(() => {
    if (cat) document.title = `${cat.label} · FLY`;
  }, [cat]);

  if (!cat) return <Navigate to="/products" replace />; // 非法品类回聚合页

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

        {/* 款式区块（品类 → 款式 → 系列） */}
        <section className="wrap">
          {fallback && (
            <p style={{ ...EMPTY_STYLE, padding: "18px 0", color: "#b07a2b" }}>
              后端服务暂不可用，以下为本地示例数据
            </p>
          )}

          {items === null && <p style={EMPTY_STYLE}>加载中…</p>}

          {items !== null && items.length === 0 && (
            <p style={EMPTY_STYLE}>该品类暂无上架款式，敬请期待。</p>
          )}

          {items !== null && items.length > 0 && (
            <>
              <div className="sec-head" style={{ marginBottom: 24 }}>
                <div>
                  <div className="eyebrow" style={{ marginBottom: 10 }}>{cat.en} · {cat.label}</div>
                  <h2 className="sec-title">当季款式</h2>
                  <p className="sec-sub">共 {items.length} 款 · 部分款式下设有系列</p>
                </div>
              </div>
              <div className="grid list-grid">
                {items.map((it) => (
                  <Link className="p-card" to={`/products/${cat.key}/${it.code}`} key={it.code}>
                    <div className="visual">
                      {it.hot && <span className="rec">主推</span>}
                      <img src={it.img} alt={it.name} loading="lazy" />
                    </div>
                    <div className="cap">
                      <b>{it.name}</b>
                      <span className="meta">{cat.label} · {it.code}</span>
                      <p>{it.desc}</p>
                      {it.series.length > 0 && (
                        <div className="chip-row" style={{ marginTop: 10 }}>
                          {it.series.map((s) => (
                            <span className="chip" key={s.id ?? s.name}>{s.name}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  </Link>
                ))}
              </div>
            </>
          )}
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
