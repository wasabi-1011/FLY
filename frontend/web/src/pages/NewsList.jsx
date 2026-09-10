import { useEffect } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import SiteNav from "../components/SiteNav.jsx";
import SiteFooter from "../components/SiteFooter.jsx";
import PageHero from "../components/PageHero.jsx";
import { formatDate, getNewsByCat } from "../data/siteData.js";

const CAT_META = {
  company:  { label: "企业新闻", en: "COMPANY NEWS", sub: "品牌发布 · 门店动态 · 企业责任", bg: "/pic/storefront-02.jpg" },
  industry: { label: "行业资讯", en: "INDUSTRY",     sub: "面料趋势 · 零售观察 · 行业洞察", bg: "/pic/storefront-03.jpg" },
};

export default function NewsList() {
  const { category } = useParams();
  const meta = CAT_META[category];
  const list = getNewsByCat(category);

  useEffect(() => { if (meta) document.title = `${meta.label} · FLY`; }, [meta]);

  if (!meta) return <Navigate to="/news/company" replace />; // 非法分类回企业新闻

  return (
    <>
      <SiteNav />
      <div className="sub-page">
        <PageHero
          crumbs={[{ label: "新闻", to: "/news/company" }, { label: meta.label }]}
          title={meta.label}
          en={meta.en}
          sub={meta.sub}
          bg={meta.bg}
        />

        {/* 分类切换 tab */}
        <div className="wrap">
          <div className="tab-bar" role="tablist" aria-label="新闻分类">
            {Object.keys(CAT_META).map(k => (
              <Link key={k} role="tab" aria-selected={category === k}
                className={`tab${category === k ? " on" : ""}`} to={`/news/${k}`}>
                {CAT_META[k].label}
              </Link>
            ))}
          </div>

          <div className="news-grid" style={{ marginTop: 32 }}>
            {list.map(n => (
              <Link className="news-card" to={`/news/${n.cat}/${n.slug}`} key={n.slug}>
                <div className="thumb"><img src={n.cover} alt={n.title} loading="lazy" /></div>
                <div className="cat">{meta.label}</div>
                <h3>{n.title}</h3>
                <p className="news-lead">{n.lead}</p>
                <div className="meta">{formatDate(n.date)} · {n.place}</div>
              </Link>
            ))}
          </div>
        </div>
      </div>
      <SiteFooter />
    </>
  );
}
