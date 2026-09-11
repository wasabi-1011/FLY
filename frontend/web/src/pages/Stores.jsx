import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import SiteNav from "../components/SiteNav.jsx";
import SiteFooter from "../components/SiteFooter.jsx";
import PageHero from "../components/PageHero.jsx";
import {
  fetchStores,
  fetchStoreCities,
  localStores,
  localCities,
  localStoreTotal,
  cityPointsFrom,
} from "../data/storesApi.js";
import { loadTMap, tmapKey, waitForLayout, observeResize } from "../data/tmapLoader.js";

// 地图 Key 统一从全局注入（index.html 里设置 window.__FLY_TMAP_KEY__），
// 不在源码里写死明文 —— 前端 Key 可被嗅探，必须在腾讯位置服务控制台配 Referer 白名单。
const TMAP_KEY = tmapKey();

const PIN_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="30" height="38" viewBox="0 0 30 38">' +
  '<path d="M15 1C7.27 1 1 7.27 1 15c0 10.5 14 22 14 22s14-11.5 14-22C29 7.27 22.73 1 15 1z" fill="#c8893f" stroke="#fff" stroke-width="2"/>' +
  '<circle cx="15" cy="15" r="6" fill="#fff"/></svg>';
const PIN_URL = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(PIN_SVG);

export default function Stores() {
  const [city, setCity] = useState("all"); // 'all' | 城市名
  const [stores, setStores] = useState([]);
  const [cities, setCities] = useState([]);
  const [offline, setOffline] = useState(false); // 接口不可用 → 已回退本地示例
  const [loaded, setLoaded] = useState(false);
  const [mapReady, setMapReady] = useState(false); // 地图就绪后才挂点位（数据可能先于地图到达）
  const mapRef = useRef(null);
  const markersRef = useRef(null);
  const iwRef = useRef(null);
  const statusRef = useRef(null); // 地图加载/错误提示区

  const total = useMemo(() => stores.length, [stores]);
  const points = useMemo(() => cityPointsFrom(stores), [stores]);

  useEffect(() => { document.title = "门店查询 · FLY"; }, []);

  /* ---------- 取数：成功但为空 → 空状态；仅失败 → 回退本地 ---------- */
  useEffect(() => {
    let alive = true;
    (async () => {
      const [sRes, cRes] = await Promise.all([fetchStores(), fetchStoreCities()]);
      if (!alive) return;
      if (sRes.ok) {
        setStores(sRes.stores);
        setOffline(false);
      } else {
        setStores(localStores());
        setOffline(true);
      }
      setCities(cRes.ok ? cRes.cities : localCities());
      setLoaded(true);
    })();
    return () => { alive = false; };
  }, []);

  const rows = useMemo(
    () => (city === "all" ? stores : stores.filter((s) => s.city === city)),
    [stores, city]
  );

  // ---- 腾讯地图初始化（与首页门店入口共用单例加载器，避免 SDK 二次注入） ----
  useEffect(() => {
    let cancelled = false;
    const say = (state) => { if (statusRef.current) statusRef.current.dataset.state = state; };

    const removeAuthBanners = () => {
      if (typeof document === "undefined" || !document.body) return; // 页面销毁后回调可能仍会触发
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
      const targets = new Set();
      let t;
      while ((t = walker.nextNode())) {
        if (!t.nodeValue || !t.nodeValue.includes("鉴权失败")) continue;
        let el = t.parentElement, guard = 0;
        while (el && guard < 4) {
          if (el.id === "storeMap" || (el.classList && el.classList.contains("store-map"))) break;
          const txt2 = (el.textContent || "").trim();
          if (txt2.length <= 120) { targets.add(el); break; }
          el = el.parentElement; guard++;
        }
      }
      targets.forEach((el) => el.remove());
    };
    const observer = new MutationObserver(() => removeAuthBanners());
    observer.observe(document.body, { childList: true, subtree: true });
    const intervalId = setInterval(removeAuthBanners, 1500);
    const stopId = setTimeout(() => { observer.disconnect(); clearInterval(intervalId); }, 12000);

    function init() {
      if (mapRef.current || typeof window.TMap === "undefined") return;
      try {
        const T = window.TMap;
        const map = new T.Map("storeMap", {
          center: new T.LatLng(34.5, 108.5), zoom: 4.4, minZoom: 3, maxZoom: 12,
          baseMap: { type: "vector", features: ["base", "building3d"] },
        });
        mapRef.current = map;
        markersRef.current = new T.MultiMarker({
          map,
          styles: { pin: new T.MarkerStyle({ width: 30, height: 38, anchor: { x: 15, y: 38 }, src: PIN_URL }) },
          geometries: [],
        });
        map.on("click", () => iwRef.current && iwRef.current.close());
        const iw = new T.InfoWindow({ map, position: new T.LatLng(34.5, 108.5), offset: { x: 0, y: -32 }, content: '<div class="iw"></div>' });
        iw.close(); iwRef.current = iw;
        map.on("tilesloaded", () => say("ready"));
        setTimeout(() => say("ready"), 2500);
        // 首帧之后布局才稳定（字体 / 图片回流）的情况，再补一次尺寸重算
        setTimeout(() => { try { if (map.resize) map.resize(); } catch (e) { /* noop */ } }, 300);
        say("loading");
        setMapReady(true); // 通知点位挂载；地图晚于数据就绪时也不会漏挂
      } catch (e) { say("error"); }
    }

    if (!TMAP_KEY) { say("error"); }
    else {
      say("loading");
      // 已加载则立刻复用（SPA 从首页跳进来时 window.TMap 通常已存在，重复注入脚本会让首屏地图失效）
      loadTMap(TMAP_KEY)
        .then(async () => {
          if (cancelled || mapRef.current) return;
          // GL 地图在 0 尺寸容器上初始化会得到不可交互的空白画布，等布局就绪再 init
          await waitForLayout(document.getElementById("storeMap"));
          if (cancelled || mapRef.current) return;
          init();
          removeAuthBanners();
          setTimeout(removeAuthBanners, 1200);
        })
        .catch(() => { if (!cancelled) say("error"); });
    }

    return () => {
      cancelled = true;
      clearTimeout(stopId); clearInterval(intervalId); observer.disconnect();
      // 不卸载全局 SDK（window.TMap）—— 与首页门店入口共用，移除脚本会打断正在使用的实例
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 容器尺寸变化（字体/图片回流、窗口缩放、首屏布局延迟）后 GL 地图不会自动重算视口
  useEffect(() => {
    return observeResize(document.getElementById("storeMap"), () => {
      try {
        if (mapRef.current && typeof mapRef.current.resize === "function") mapRef.current.resize();
      } catch (e) { /* noop */ }
    });
  }, []);

  const flyTo = useCallback((name) => {
    setCity(name);
    const p = points.find((x) => x.city === name);
    if (!p || !mapRef.current || !window.TMap) return;
    mapRef.current.easeTo({ center: new window.TMap.LatLng(p.lat, p.lng), zoom: 9.5, duration: 600 });
    const lis = stores.filter((s) => s.city === name)
      .map((s) => `<li>${s.name} · ${s.addr}</li>`).join("");
    const info = iwRef.current;
    if (info) {
      info.setPosition(new window.TMap.LatLng(p.lat, p.lng));
      info.setContent(`<div class="iw"><b>${name}</b><div class="sub">${p.count} 家门店</div><ul>${lis}</ul></div>`);
      info.open();
    }
  }, [points, stores]);

  // 点位随数据更新：门店数据是异步到达的，地图也可能后到 —— mapReady 变化时重挂，确保不漏
  useEffect(() => {
    if (!mapReady || !mapRef.current || !markersRef.current || !window.TMap) return;
    const mk = markersRef.current;
    mk.setGeometries(
      points.map((p) => ({
        id: p.city, styleId: "pin", position: new window.TMap.LatLng(p.lat, p.lng),
        properties: { city: p.city },
      }))
    );
    const handler = (e) => {
      const g = (e && e.geometry) || {};
      flyTo((g.properties && g.properties.city) || g.id);
    };
    mk.on("click", handler);
    return () => { try { if (mk.off) mk.off("click", handler); } catch (e) { /* 旧版 SDK 可能无 off */ } };
  }, [mapReady, points, flyTo]);

  const resetAll = () => {
    setCity("all");
    if (mapRef.current && window.TMap) {
      mapRef.current.easeTo({ center: new window.TMap.LatLng(34.5, 108.5), zoom: 4.4, duration: 600 });
      if (iwRef.current) iwRef.current.close();
    }
  };

  return (
    <>
      <SiteNav />
      <div className="sub-page stores-page">
        <PageHero
          crumbs={[{ label: "门店" }]}
          title="门店地图"
          en="STORES"
          sub={`全国 ${cities.length} 城 ${total} 家门店 · 点选城市或图钉查看门店`}
          bg="/pic/storefront-01.jpg"
        />

        {offline && (
          <div className="wrap">
            <div className="news-note">
              门店服务暂不可用，以下为本地示例数据（后台启动后自动切换为真实门店）。
            </div>
          </div>
        )}

        {/* 城市联动 chips */}
        <div className="wrap">
          <div className="store-chips" role="tablist" aria-label="按城市筛选门店">
            <button role="tab" aria-selected={city === "all"} className={`chip${city === "all" ? " on" : ""}`}
              onClick={resetAll}>全部 · {total}</button>
            {cities.map((c) => (
              <button role="tab" aria-selected={city === c.city} className={`chip${city === c.city ? " on" : ""}`}
                key={c.city} onClick={() => flyTo(c.city)}>{c.city} · {c.count}</button>
            ))}
          </div>
        </div>

        {/* 大图地图 */}
        <div className="wrap">
          <div className="store-map big-map" aria-label="中国门店分布大地图">
            <div id="storeMap" role="application" aria-label="中国地图门店点位"></div>
            <div className="map-hint">点击城市标记 / 门店卡查看门店 · 拖拽平移 · 滚轮缩放</div>
            <div className="map-status" ref={statusRef} data-state="loading">
              <span className="spin"></span>
              <div className="st-load">正在加载中国底图…</div>
              <div className="st-err"><b>底图加载失败</b><div>未配置地图 Key 或网络不可用。门店列表仍可正常浏览。</div></div>
            </div>
          </div>
        </div>

        {/* 门店列表 */}
        <section className="wrap">
          <div className="sec-head" style={{ marginTop: 8 }}>
            <div>
              <div className="eyebrow" style={{ marginBottom: 10 }}>{city === "all" ? "全部城市" : `当前城市 · ${city}`}</div>
              <h2 className="sec-title">{city === "all" ? "全部门店" : city} <small className="count">共 {rows.length} 家</small></h2>
            </div>
            {city !== "all" && <button className="chip" onClick={resetAll}>显示全部城市</button>}
          </div>
          {loaded && !rows.length ? (
            <div className="news-empty">暂无门店数据。</div>
          ) : (
            <div className="store-grid">
              {rows.map((s, i) => (
                <button className="store-card" key={s.id ?? i} onClick={() => flyTo(s.city)}>
                  <span className="badge">{s.city}{s.typeText ? ` · ${s.typeText}` : ""}</span>
                  <b>{s.name}</b>
                  <span className="addr">{s.addr}</span>
                  <span className="hours">{s.hours ? `营业时间 ${s.hours}` : "营业时间请电话咨询"}</span>
                  <span className="goto">地图定位 →</span>
                </button>
              ))}
            </div>
          )}
        </section>
      </div>
      <SiteFooter />
    </>
  );
}
