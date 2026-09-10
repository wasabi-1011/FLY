import { useState } from "react";
import { Link, useLocation } from "react-router-dom";

// 主导航结构：to=真实路由；soon=true 表示页面未上线（渲染"建设中"占位，不做死链）
// activePrefix 用于当前栏目高亮判断
const NAV = [
  { key: "products", label: "产品", activePrefix: "/products", menu: true, sub: [
    { label: "女装", to: "/products/women" },
    { label: "男装", to: "/products/men" },
    { label: "童装", to: "/products/kids" },
    { label: "热门推荐", to: "/products/hot" },
  ] },
  { key: "stores", label: "门店", activePrefix: "/stores", sub: [
    { label: "门店地图与列表", to: "/stores" },
  ] },
  { key: "news", label: "新闻", activePrefix: "/news", menu: true, sub: [
    { label: "企业新闻", to: "/news/company" },
    { label: "行业资讯", to: "/news/industry" },
  ] },
  { key: "join", label: "招聘", soon: true, soonText: "建设中", sub: [
    { label: "社会招聘" }, { label: "校园招聘" },
  ] },
  { key: "about", label: "关于我们", activePrefixes: ["/about", "/contact"], sub: [
    { label: "关于 FLY", to: "/about" },
    { label: "品牌介绍", to: "/about/brand" },
    { label: "发展历程", to: "/about/history" },
    { label: "联系我们", to: "/contact" },
  ] },
];

export default function SiteNav() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [openItem, setOpenItem] = useState(null);
  const { pathname } = useLocation();

  const isActive = (item) => (item.activePrefix ? pathname.startsWith(item.activePrefix) : false);

  const renderSub = (item) =>
    item.soon
      ? item.sub.map((s, j) => (
          <span className="drop-soon" key={j}>{s.label}<i>建设中</i></span>
        ))
      : item.sub.map((s, j) => (
          <Link key={j} to={s.to} onClick={() => setDrawerOpen(false)}>{s.label}</Link>
        ));

  return (
    <>
      <header className="site-nav">
        <div className="wrap nav-inner">
          <Link className="brand" to="/" aria-label="返回首页">
            <svg className="logo" viewBox="0 0 26 26" fill="none" stroke="#0F172A" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
              <path d="M13 2 L23 24 H18 L13 10 L8 24 H3 Z" />
            </svg>
            <b>FLY</b>
          </Link>

          <nav className="nav-links" aria-label="主导航">
            {NAV.map((item, i) => (
              <div className={`nav-item${isActive(item) ? " active" : ""}`} key={item.key}>
                {item.soon ? (
                  <a href="#" onClick={(e) => e.preventDefault()} aria-disabled="true" title={`${item.label}·${item.soonText}`} style={{ opacity: 0.62 }}>
                    {item.label} <span className="chev"></span>
                  </a>
                ) : (
                  <Link to={item.activePrefix}>{item.label} <span className="chev"></span></Link>
                )}
                <div className="dropdown">{renderSub(item)}</div>
              </div>
            ))}
          </nav>

          <div className="nav-actions">
            <button className="icon-btn search-cta" aria-label="全站搜索（建设中）"
              onClick={() => alert("全站搜索建设中，敬请期待")}>
              <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7" /><path d="M20 20 L16.5 16.5" /></svg>
            </button>
            <button className={`hamburger${drawerOpen ? " open" : ""}`} aria-label={drawerOpen ? "关闭菜单" : "打开菜单"}
              aria-expanded={drawerOpen} onClick={() => setDrawerOpen(o => !o)}>
              <span></span><span></span><span></span>
            </button>
          </div>
        </div>
      </header>

      {/* 移动端抽屉 */}
      <div className={`drawer${drawerOpen ? " open" : ""}`}>
        {NAV.map((item, i) => (
          <div className={`m-item${openItem === i ? " open" : ""}`} key={item.key}>
            <div className="m-head" onClick={() => setOpenItem(openItem === i ? null : i)}>
              {item.label}
              {item.soon && <span className="soon-chip">建设中</span>}
              <span className="m-chev"></span>
            </div>
            <div className="m-sub">
              {item.soon
                ? item.sub.map((s, j) => (
                    <span className="m-dim" key={j}>{s.label}（建设中）</span>
                  ))
                : item.sub.map((s, j) => (
                    <Link key={j} to={s.to} onClick={() => setDrawerOpen(false)}>{s.label}</Link>
                  ))}
            </div>
          </div>
        ))}
        <div className="m-cta">
          <button className="btn" onClick={() => alert("全站搜索建设中，敬请期待")}>搜索全站</button>
        </div>
      </div>
    </>
  );
}
