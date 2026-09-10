import { Link } from "react-router-dom";

// 二级页公共页头：面包屑 + 标题(中英) + 副题，可选背景大图
// crumbs: [{label, to?}] 末级不传 to 即当前页纯文本
export default function PageHero({ crumbs = [], title, en, sub, bg, dark = false }) {
  return (
    <div className={`sub-hero${dark ? " dark" : ""}`}>
      {bg && <div className="sh-bg" style={{ backgroundImage: `url(${bg})` }} aria-hidden="true"></div>}
      <div className="wrap sh-inner">
        <nav className="crumb" aria-label="面包屑">
          <Link to="/">首页</Link>
          {crumbs.map((c, i) => (
            <span key={i}>
              <i className="sep">›</i>
              {c.to ? <Link to={c.to}>{c.label}</Link> : <em aria-current="page">{c.label}</em>}
            </span>
          ))}
        </nav>
        <h1 className="sh-title">{title}</h1>
        {en && <div className="sh-en">{en}</div>}
        {sub && <p className="sh-sub">{sub}</p>}
      </div>
    </div>
  );
}
