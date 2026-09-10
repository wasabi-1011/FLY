import { useEffect } from "react";
import { Link } from "react-router-dom";
import SiteNav from "../components/SiteNav.jsx";
import SiteFooter from "../components/SiteFooter.jsx";
import PageHero from "../components/PageHero.jsx";
import AboutTabs from "../components/AboutTabs.jsx";
import { BRAND_IDENTITY } from "../data/aboutData.js";

// /about/brand 品牌介绍：标识释义 · 设计语言 · 标准色示意
export default function AboutBrand() {
  useEffect(() => { document.title = "品牌介绍 · FLY"; }, []);

  return (
    <>
      <SiteNav />
      <div className="sub-page">
        <PageHero
          crumbs={[{ label: "关于我们", to: "/about" }, { label: "品牌介绍" }]}
          title="品牌介绍"
          en="BRAND IDENTITY"
          sub="标识、设计语言与色彩 —— FLY 如何被看见与记住"
          bg="/pic/storefront-02.jpg"
        />
        <div className="wrap">
          <AboutTabs />

          {/* 标识释义 */}
          <section className="about-brand-sec">
            <div className="brand-sec-txt">
              <div className="eyebrow" style={{ marginBottom: 12 }}>品牌标识 · LOGO</div>
              <h3 className="brand-sec-title">一枚向上展开的翼</h3>
              <p>{BRAND_IDENTITY.intro}</p>
              <div className="kw-row">
                {BRAND_IDENTITY.keywords.map((k) => <span className="kw" key={k}>{k}</span>)}
              </div>
            </div>
            <div className="brand-mark" aria-label="FLY 品牌标识示意">
              <svg className="mark-logo" viewBox="0 0 26 26" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M13 2 L23 24 H18 L13 10 L8 24 H3 Z" />
              </svg>
              <b className="mark-word">FLY</b>
              <span className="mark-motto">{BRAND_IDENTITY.mottoEn}</span>
            </div>
          </section>

          {/* 设计语言 */}
          <section className="about-brand-sec flip">
            <div className="brand-sec-txt">
              <div className="eyebrow" style={{ marginBottom: 12 }}>设计语言 · DESIGN</div>
              <h3 className="brand-sec-title">都市游牧：克制中的应对力</h3>
              <p>{BRAND_IDENTITY.design}</p>
            </div>
            <div className="brand-swatch">
              <span className="swatch-title">标准色示意</span>
              <ul>
                {BRAND_IDENTITY.swatches.map((sw) => (
                  <li key={sw.name} className={`sw ${sw.cls}`}>
                    <i style={{ background: sw.hex }} aria-hidden="true"></i>
                    <b>{sw.name}</b>
                    <em>{sw.hex}</em>
                  </li>
                ))}
              </ul>
            </div>
          </section>

          {/* 底部引导 */}
          <div className="cta-line" style={{ padding: "8px 0 60px" }}>
            <Link className="more" to="/about">回到关于 FLY ←</Link>
            <Link className="more" to="/about/history">看看发展历程 →</Link>
          </div>
        </div>
      </div>
      <SiteFooter />
    </>
  );
}
