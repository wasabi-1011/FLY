import { useEffect, useRef, useState } from "react";

// 兜底帧：后端不可用或首页尚未配置轮播时使用（与原视觉一致）
const FALLBACK = [
  { kicker: "FLY · 2026 秋冬 · 城野机能", title: "FLY",
    sub: "FEEL · LIVE · YOURSELF", cn: "穿出自我，随心而飞", image: "", link: "" },
  { kicker: "CITY WILD", title: "城野机能",
    sub: "URBAN MEETS WILD · 2026A/W", cn: "城市与山野，同频共振", image: "", link: "" },
  { kicker: "NEW STORE", title: "深圳万象天地旗舰店",
    sub: "OPENING · GRAND DAY", cn: "让「看到」变为「找到」", image: "", link: "" },
];

// 副标题：中文用衬线字距样式，英文沿用宽字距样式
const hasCJK = (s) => /[\u4e00-\u9fa5]/.test(s || "");
const DEFAULT_LINK = "/products";
const DEFAULT_SUB = "穿出自我，随心而飞";

// 后台「网页管理 → 首页轮播图」保存的帧结构（/api/content/home 的 FULLSCREEN_VISUAL）
const fromFrame = (f) => ({
  image: f.image || "",
  kicker: f.kicker || "",
  title: f.title || (f.layers && f.layers[0] ? f.layers[0].text : "") || "",
  sub: f.sub || (f.layers && f.layers[1] ? f.layers[1].text : "") || "",
  cn: f.cn || (f.layers && f.layers[2] ? f.layers[2].text : "") || "",
  link: f.link || "",
});

export default function Hero() {
  const [slides, setSlides] = useState(FALLBACK);
  const total = slides.length;
  const [cur, setCur] = useState(0);
  const timer = useRef(null);

  // 读取后端已发布的首页轮播；失败/无数据则保持兜底帧
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await fetch("/api/content/home");
        if (!res.ok) return;
        const data = await res.json();
        const block = (data.blocks || []).find((b) => b.type === "FULLSCREEN_VISUAL");
        const frames = ((block && block.config_json && block.config_json.frames) || [])
          .filter((f) => f.active !== false);
        if (alive && frames.length) setSlides(frames.map(fromFrame));
      } catch (e) {
        // 后端不可用时静默降级为本地帧
      }
    })();
    return () => { alive = false; };
  }, []);

  const go = (n) => setCur(((n % total) + total) % total);
  const start = () => { stop(); timer.current = setInterval(() => setCur(c => (c + 1) % total), 5000); };
  const stop = () => { if (timer.current) clearInterval(timer.current); };

  useEffect(() => { start(); return stop; }, [total]);

  const restart = () => { stop(); start(); };

  return (
    <section className="hero" id="home" aria-label="首屏全屏轮播"
      onMouseEnter={stop} onMouseLeave={start}>
      {slides.map((s, i) => (
        <div className={`slide${s.image ? "" : " slide" + ((i % 3) + 1)}${i === cur ? " active" : ""}`} key={i} data-idx={i}>
          <div className="bg" style={s.image ? { backgroundImage: `url("${s.image}")` } : undefined}></div>
          <div className="slide-content">
            {s.kicker ? <div className="frame-kicker">{s.kicker}</div> : null}
            <h1 className="frame-title" style={s.title && s.title.length > 8 ? { fontSize: "clamp(34px,6vw,64px)", letterSpacing: ".1em" } : undefined}>{s.title}</h1>
            {s.sub ? <div className={hasCJK(s.sub) ? "frame-cn" : "frame-sub"}>{s.sub}</div> : null}
            {s.cn && s.cn !== s.sub ? <div className="frame-cn">{s.cn}</div> : null}
            {!s.sub && !s.cn ? <div className="frame-cn">{DEFAULT_SUB}</div> : null}
            <a className="frame-cta" href={s.link || DEFAULT_LINK}>了解更多</a>
          </div>
        </div>
      ))}

      <button className="car-arrow prev" aria-label="上一帧" onClick={() => { go(cur - 1); restart(); }}>
        <svg viewBox="0 0 24 24"><path d="M15 6l-6 6 6 6" /></svg>
      </button>
      <button className="car-arrow next" aria-label="下一帧" onClick={() => { go(cur + 1); restart(); }}>
        <svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6" /></svg>
      </button>

      <div className="hero-dots">
        {slides.map((_, i) => (
          <span key={i} className={`dot${i === cur ? " active" : ""}`} role="button" tabIndex={0}
            aria-label={`第${i + 1}帧`} onClick={() => { go(i); restart(); }} />
        ))}
      </div>
    </section>
  );
}
