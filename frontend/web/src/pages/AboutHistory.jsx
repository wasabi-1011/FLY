import { useEffect } from "react";
import { Link } from "react-router-dom";
import SiteNav from "../components/SiteNav.jsx";
import SiteFooter from "../components/SiteFooter.jsx";
import PageHero from "../components/PageHero.jsx";
import AboutTabs from "../components/AboutTabs.jsx";
import { MILESTONES } from "../data/aboutData.js";

// /about/history 发展历程：时间轴
export default function AboutHistory() {
  useEffect(() => { document.title = "发展历程 · FLY"; }, []);

  return (
    <>
      <SiteNav />
      <div className="sub-page">
        <PageHero
          crumbs={[{ label: "关于我们", to: "/about" }, { label: "发展历程" }]}
          title="发展历程"
          en="MILESTONES"
          sub="2019 — 2026 · 与城市一起生长"
          bg="/pic/storefront-03.jpg"
        />
        <div className="wrap">
          <AboutTabs />

          <section className="history" aria-label="发展历程时间轴">
            {MILESTONES.map((m, i) => (
              <div className="mile" key={m.year}>
                <div className="mile-line">
                  <span className="dot" aria-hidden="true"></span>
                  {i < MILESTONES.length - 1 && <span className="stem" aria-hidden="true"></span>}
                </div>
                <div className="mile-card">
                  <time className="mile-year">{m.year}</time>
                  <h3>{m.t}</h3>
                  <p>{m.d}</p>
                </div>
              </div>
            ))}
          </section>

          <div className="cta-line" style={{ padding: "8px 0 60px" }}>
            <Link className="more" to="/about">关于我们的起点 ←</Link>
            <Link className="more" to="/contact">想聊聊合作？联系我们 →</Link>
          </div>
        </div>
      </div>
      <SiteFooter />
    </>
  );
}
