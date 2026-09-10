import { Link } from "react-router-dom";

// 页脚栏目：to=真实路由；无页面的以占位文本呈现（建设中）
const FOOT_LINKS = {
  products: [
    { label: "女装", to: "/products/women" },
    { label: "男装", to: "/products/men" },
    { label: "童装", to: "/products/kids" },
    { label: "热门推荐", to: "/products/hot" },
  ],
  storeNews: [
    { label: "门店查询", to: "/stores" },
    { label: "企业新闻", to: "/news/company" },
    { label: "行业资讯", to: "/news/industry" },
  ],
  join: ["社会招聘", "校园招聘"],
  about: ["关于 FLY", "品牌介绍", "发展历程", "联系我们"],
};

export default function SiteFooter() {
  return (
    <footer>
      <div className="wrap">
        <div className="foot-grid">
          <div>
            <Link className="foot-brand" to="/">FLY<small>FEEL · LIVE · YOURSELF</small></Link>
            <div className="foot-social">
              <button className="icon-btn" aria-label="微博">
                <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><path d="M8 12a4 4 0 0 1 8 0M9 13.5v.01" /></svg>
              </button>
              <button className="icon-btn" aria-label="小红书">
                <svg viewBox="0 0 24 24"><path d="M8 4l8 8-8-8M8 20l8-8-8 8" /></svg>
              </button>
              <button className="icon-btn" aria-label="微信">
                <svg viewBox="0 0 24 24"><path d="M9 6a5 5 0 0 0-5 5c0 1.4.6 2.7 1.6 3.6l-.5 1.9 2.1-1A5 5 0 0 0 9 16" /><path d="M15 4a6 6 0 0 1 5 6c0 1.7-.7 3.2-1.8 4.3l.5 2-2.3-1.1" /></svg>
              </button>
            </div>
          </div>
          <div className="foot-col">
            <h5>产品</h5>
            {FOOT_LINKS.products.map(l => <Link key={l.label} to={l.to}>{l.label}</Link>)}
          </div>
          <div className="foot-col">
            <h5>门店 · 新闻</h5>
            {FOOT_LINKS.storeNews.map(l => <Link key={l.label} to={l.to}>{l.label}</Link>)}
          </div>
          <div className="foot-col">
            <h5>招聘</h5>
            {FOOT_LINKS.join.map(l => <span className="foot-dim" key={l}>{l}（建设中）</span>)}
          </div>
          <div className="foot-col">
            <h5>关于我们</h5>
            {FOOT_LINKS.about.map(l => <Link key={l.label} to={l.to}>{l.label}</Link>)}
          </div>
        </div>
        <div className="foot-bottom">
          <span>© 2026 FLY 服饰有限公司 · 保留所有权利</span>
          <span>
            <a href="#privacy" onClick={e => e.preventDefault()}>隐私政策</a> · <a href="#legal" onClick={e => e.preventDefault()}>法律声明</a> · <a href="#coop" onClick={e => e.preventDefault()}>联系合作</a> · 沪ICP备XXXXXXXX号
          </span>
        </div>
      </div>

      {/* 移动端底部固定「门店」入口 */}
      <Link className="m-store-fab" to="/stores">
        <svg viewBox="0 0 24 24"><path d="M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11Z" /><circle cx="12" cy="10" r="2.5" /></svg>
        查门店
      </Link>
    </footer>
  );
}
