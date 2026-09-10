import { useEffect } from "react";
import { Link } from "react-router-dom";
import SiteNav from "../components/SiteNav.jsx";
import SiteFooter from "../components/SiteFooter.jsx";
import PageHero from "../components/PageHero.jsx";
import AboutTabs from "../components/AboutTabs.jsx";
import { BRAND_STORY } from "../data/aboutData.js";

// /about 关于 FLY：品牌故事 · 三大价值 · 品牌数据
export default function AboutStory() {
  useEffect(() => { document.title = "关于 FLY · FLY"; }, []);

  return (
    <>
      <SiteNav />
      <div className="sub-page">
        <PageHero
          crumbs={[{ label: "关于我们", to: "/about" }, { label: "关于 FLY" }]}
          title="关于 FLY"
          en="ABOUT FLY"
          sub="穿出自我，随心而飞 —— 关于我们是谁、相信什么、走向哪里"
          bg="/pic/storefront-01.jpg"
        />
        <div className="wrap">
          <AboutTabs />

          {/* 品牌主张引语 */}
          <section className="about-lead">
            <span className="q-mark">“</span>
            <p>{BRAND_STORY.lead}</p>
            <span className="q-mark r">”</span>
          </section>

          {/* 故事正文 + 配图 */}
          <section className="about-story">
            <div className="story-txt">
              {BRAND_STORY.body.map((b, i) =>
                b.t === "h" ? <h3 key={i}>{b.v}</h3> : <p key={i}>{b.v}</p>
              )}
              <p className="story-more">
                沿着时间往回看，FLY 走过的每一步都写在<Link to="/about/history">发展历程</Link>里；
                关于品牌标识与设计语言，见<Link to="/about/brand">品牌介绍</Link>。
              </p>
            </div>
            <figure className="story-img">
              <img src="/pic/brand.jpg" alt="FLY 品牌影像" loading="lazy" />
              <figcaption>城市与旷野之间，FLY 的起点（示例图）</figcaption>
            </figure>
          </section>

          {/* 三大价值支柱 */}
          <section className="about-vals" aria-label="三大价值支柱">
            {BRAND_STORY.values.map((v, i) => (
              <article key={i} className="val-card">
                <span className="val-no">0{i + 1}</span>
                <h3>{v.t}</h3>
                <p>{v.d}</p>
              </article>
            ))}
          </section>

          {/* 品牌数据条（深色） */}
          <section className="about-stats" aria-label="品牌数据">
            {BRAND_STORY.stats.map((s, i) => (
              <div className="stat" key={i}>
                <b>{s.n}</b>
                <span>{s.l}</span>
              </div>
            ))}
          </section>

          {/* 底部引导 */}
          <div className="cta-line" style={{ padding: "8px 0 60px" }}>
            <Link className="more" to="/about/history">查看发展历程 →</Link>
            <Link className="more" to="/contact">联系我们 →</Link>
          </div>
        </div>
      </div>
      <SiteFooter />
    </>
  );
}
