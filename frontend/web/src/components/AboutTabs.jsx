import { Link, useLocation } from "react-router-dom";

// 关于我们/联系 共享子导航（用于四个固定页之间互跳，当前项高亮）
const TABS = [
  { label: "关于 FLY", to: "/about" },
  { label: "品牌介绍", to: "/about/brand" },
  { label: "发展历程", to: "/about/history" },
  { label: "联系我们", to: "/contact" },
];

export default function AboutTabs() {
  const { pathname } = useLocation();
  return (
    <nav className="tab-bar about-tabs" aria-label="关于我们子栏目">
      {TABS.map((t) => (
        <Link key={t.to} className={`tab${pathname === t.to ? " on" : ""}`} to={t.to} aria-current={pathname === t.to ? "page" : undefined}>
          {t.label}
        </Link>
      ))}
    </nav>
  );
}
