import { useEffect, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import SiteNav from "../components/SiteNav.jsx";
import SiteFooter from "../components/SiteFooter.jsx";
import { getCategory } from "../data/siteData.js";
import {
  fetchItemDetail,
  localFindItem,
  localItemsByCat,
  localRelated,
  relatedFrom,
} from "../data/productsApi.js";

// 单品详情页：左图右文（用户指定版式）
// URL：/products/:category/:code（如 /products/women/CO-SW001）
// 层级 v2.0：款式是主体，系列挂在款式下（选填），详情页下方单独列出。
export default function ItemDetail() {
  const { category, code } = useParams();
  const [state, setState] = useState({ loading: true, found: null, fallback: false, all: [] });
  // 当前查看的系列（点击「系列名称」链接后弹出系列图片；到这一层就是款式层级的最底层，不再往下跳）
  const [activeSeries, setActiveSeries] = useState(null);

  useEffect(() => {
    if (!category || !code) return;
    let alive = true;
    setActiveSeries(null);
    setState({ loading: true, found: null, fallback: false, all: [] });
    fetchItemDetail(category, code).then((res) => {
      if (!alive) return;
      if (res.ok) {
        // 接口成功：找不到 → 认为已下架/不存在（跳回产品中心，不回退本地）
        setState({ loading: false, found: res.found, fallback: false, all: res.items || [] });
      } else {
        // 仅接口失败才回退本地示例
        setState({
          loading: false,
          found: localFindItem(category, code),
          fallback: true,
          all: localItemsByCat(category),
        });
      }
    });
    return () => { alive = false; };
  }, [category, code]);

  const found = state.found;
  useEffect(() => {
    if (found) document.title = `${found.item.name} · ${found.item.series[0]?.name || getCategory(category)?.label} · FLY`;
  }, [found, category]);

  // 系列图片查看层：Esc 关闭
  useEffect(() => {
    if (!activeSeries) return undefined;
    const onKey = (e) => { if (e.key === "Escape") setActiveSeries(null); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [activeSeries]);

  if (state.loading) {
    return (
      <>
        <SiteNav />
        <div className="sub-page">
          <div className="wrap" style={{ padding: "90px 0", textAlign: "center", color: "#8a8a8a" }}>加载中…</div>
        </div>
        <SiteFooter />
      </>
    );
  }

  if (!found) return <Navigate to="/products" replace />; // 非法品类/款号/已下架 → 回产品中心

  const cat = getCategory(category);
  const item = found.item;
  const itemSeries = item.series || [];
  const related = state.fallback ? localRelated(category, code) : relatedFrom(state.all, category, code);
  const more = state.all.filter((i) => i.cat === cat.key).length;
  const specRows = [
    { k: "面料", v: item.fabric },
    { k: "版型", v: item.fit },
    { k: "护理", v: item.care },
  ].filter((r) => r.v);

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

          {state.fallback && (
            <p style={{ margin: "8px 0 0", color: "#b07a2b", fontSize: 13 }}>后端服务暂不可用，以下为本地示例数据</p>
          )}

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
                {cat.label}
                {itemSeries[0]?.name ? ` · ${itemSeries[0].name}` : ""}
                {itemSeries[0]?.season ? ` · ${itemSeries[0].season}` : ""}
              </div>
              <h1 className="id-name">{item.name}</h1>
              <div className="id-code">
                款号 {item.code}
                {item.hot && <span className="tag" style={{ marginLeft: 10 }}>主推</span>}
              </div>

              {item.desc && <p className="id-lead">{item.desc}</p>}
              {item.story && <p className="id-story">{item.story}</p>}

              {(item.points || []).length > 0 && (
                <>
                  <h2 className="id-h2">设计要点</h2>
                  <ul className="id-points">
                    {item.points.map((p, i) => <li key={i}>{p}</li>)}
                  </ul>
                </>
              )}

              <div className="id-specs">
                {specRows.map((r) => (
                  <div className="spec" key={r.k}><dt>{r.k}</dt><dd>{r.v}</dd></div>
                ))}
              </div>

              <div className="id-nav">
                <Link className="btn ghost" to={`/products/${cat.key}`}>← 返回{cat.label}</Link>
                <Link className="btn" to="/stores">到店体验 · 查门店</Link>
              </div>
            </div>
          </div>

          {/* 旗下系列（挂在款式下，选填）：仅以「系列名称」链接呈现，点击查看系列图片（层级最底层） */}
          {itemSeries.length > 0 && (
            <section className="id-series" aria-label="旗下系列">
              <div className="sec-head" style={{ marginBottom: 20 }}>
                <div>
                  <div className="eyebrow" style={{ marginBottom: 10 }}>系列</div>
                  <h2 className="sec-title">旗下系列</h2>
                  <p className="sec-sub">
                    该款式共 {itemSeries.length} 个系列 · 点击系列名称查看系列图片
                  </p>
                </div>
              </div>
              <ul className="series-links">
                {itemSeries.map((s) => (
                  <li key={s.id ?? s.name}>
                    <button
                      type="button"
                      className="series-link"
                      onClick={() => setActiveSeries(s)}
                      aria-label={`查看系列「${s.name}」的图片`}
                    >
                      {s.name}
                      {s.season && <span className="meta">{s.season}</span>}
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* 相关推荐：同品类其它款 */}
          {related.length > 0 && (
            <section className="id-related" aria-label="相关款式推荐" style={{ marginTop: 46 }}>
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

      {/* 系列图片查看层（系列层级最底层：只看图，不再往下跳） */}
      {activeSeries && (
        <div
          className="series-viewer"
          role="dialog"
          aria-modal="true"
          aria-label={`系列「${activeSeries.name}」图片`}
          onClick={(e) => { if (e.target === e.currentTarget) setActiveSeries(null); }}
        >
          <div className="sv-box">
            <button type="button" className="sv-x" onClick={() => setActiveSeries(null)} aria-label="关闭">×</button>
            <div className="sv-media">
              <img src={activeSeries.cover} alt={`${activeSeries.name} 系列图片`} />
            </div>
            <div className="sv-cap">
              <b>{activeSeries.name}</b>
              <span className="meta">
                {[cat.label, activeSeries.season].filter(Boolean).join(" · ")}
              </span>
            </div>
          </div>
        </div>
      )}
      <SiteFooter />
    </>
  );
}
