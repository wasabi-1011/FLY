/* 腾讯地图 GL JS · 单例加载器
 *
 * 为什么需要它（对应线上问题「首页地图正常、/stores 首次进入选点不灵、刷新后正常」）：
 * 1) 首页门店入口与门店地图页共用同一份 SDK。SPA 客户端路由跳转时 window.TMap 往往已经存在，
 *    若组件再注入一次 <script>，GL JS 会被二次加载，地图首屏偶发不可用 —— 整页刷新（只加载一次）就正常。
 *    这里统一成「已加载 → 复用；加载中 → 等同一个 Promise；未加载 → 只注入一次」。
 * 2) GL 地图在尺寸为 0 的容器上初始化，会得到一张不可交互的空白画布。等容器真正有尺寸再 init。
 *
 * Key 仍只从 window.__FLY_TMAP_KEY__ 读（frontend/web/index.html 注入），组件内不写明文。
 */

export const TMAP_SDK_URL = "https://map.qq.com/api/gljs?v=1.exp";
const SCRIPT_MARK = "map.qq.com/api/gljs";

let pending = null;

export function tmapKey() {
  if (typeof window === "undefined") return "";
  return window.__FLY_TMAP_KEY__ || "";
}

function existingScript() {
  if (typeof document === "undefined") return null;
  const list = document.querySelectorAll("script[src]");
  for (let i = 0; i < list.length; i++) {
    const src = list[i].src || "";
    if (src.indexOf(SCRIPT_MARK) > -1) return list[i];
  }
  return null;
}

/** 加载腾讯地图 SDK；已加载则立即 resolve(TMap)，永不复重复注入脚本。 */
export function loadTMap(key, timeout = 15000) {
  if (typeof window === "undefined") return Promise.reject(new Error("no-window"));
  if (window.TMap) return Promise.resolve(window.TMap);
  if (pending) return pending;

  const k = key || tmapKey();
  if (!k) return Promise.reject(new Error("no-tmap-key"));

  pending = new Promise((resolve, reject) => {
    const startedAt = Date.now();
    const poll = () => {
      if (window.TMap) { resolve(window.TMap); return; }
      if (Date.now() - startedAt > timeout) { reject(new Error("tmap-load-timeout")); return; }
      setTimeout(poll, 150);
    };
    const found = existingScript();
    if (found) {
      // 页面上已有（可能在别的组件注入过、也可能正在加载）：只等，不重复注入
      found.addEventListener("error", () => reject(new Error("tmap-script-error")));
    } else {
      const s = document.createElement("script");
      s.src = `${TMAP_SDK_URL}&key=${encodeURIComponent(k)}`;
      s.async = true;
      s.onerror = () => reject(new Error("tmap-script-error"));
      document.head.appendChild(s);
    }
    poll();
  }).catch((err) => { pending = null; throw err; });

  return pending;
}

/** 等容器拿到真实尺寸（GL 地图在 0 尺寸容器上初始化会变成不可交互的空白画布）。 */
export function waitForLayout(el, tries = 60) {
  return new Promise((resolve) => {
    if (typeof requestAnimationFrame === "undefined") { resolve(!!el); return; }
    let left = tries;
    const step = () => {
      if (!el) { resolve(false); return; }
      if (el.clientWidth > 0 && el.clientHeight > 0) { resolve(true); return; }
      if (--left <= 0) { resolve(false); return; }
      requestAnimationFrame(step);
    };
    step();
  });
}

/** 容器尺寸变化后 GL 地图不会自动重算视口，需显式 resize。返回清理函数。 */
export function observeResize(el, onChange) {
  if (!el || typeof ResizeObserver === "undefined") return () => {};
  let raf = 0;
  const ro = new ResizeObserver(() => {
    if (raf) return;
    raf = requestAnimationFrame(() => { raf = 0; onChange(); });
  });
  ro.observe(el);
  return () => { if (raf) cancelAnimationFrame(raf); ro.disconnect(); };
}
