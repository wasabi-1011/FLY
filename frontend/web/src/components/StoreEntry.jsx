import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchStores,
  fetchStoreCities,
  localStores,
  localCities,
  cityPointsFrom,
} from "../data/storesApi.js";
import { loadTMap, tmapKey, waitForLayout, observeResize } from "../data/tmapLoader.js";

// 地图 Key 与门店地图页共用同一处注入（frontend/web/index.html 的 window.__FLY_TMAP_KEY__），
// 组件内不再硬编码 —— 以前这里写死过一个 Key，导致「首页能加载地图、/stores 不能」的诡异差异。
const TMAP_KEY = tmapKey();

const PIN_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="30" height="38" viewBox="0 0 30 38">' +
  '<path d="M15 1C7.27 1 1 7.27 1 15c0 10.5 14 22 14 22s14-11.5 14-22C29 7.27 22.73 1 15 1z" fill="#c8893f" stroke="#fff" stroke-width="2"/>' +
  '<circle cx="15" cy="15" r="6" fill="#fff"/></svg>';
const PIN_URL = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(PIN_SVG);

export default function StoreEntry() {
  const [search, setSearch] = useState("");
  const [stores, setStores] = useState([]);
  const [cityCounts, setCityCounts] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const [mapReady, setMapReady] = useState(false); // 地图就绪后才挂点位（数据可能先于地图到达）
  const [activeCity, setActiveCity] = useState(null);
  const mapRef = useRef(null);
  const markersRef = useRef(null);
  const infoRef = useRef(null);
  const loadingRef = useRef(null);
  const errorRef = useRef(null);
  const openCityRef = useRef(null);

  /* ---------- 取数：与门店地图页同一套接口，空 vs 失败约定一致 ---------- */
  useEffect(() => {
    let alive = true;
    (async () => {
      const sRes = await fetchStores();
      if (!alive) return;
      setStores(sRes.ok ? sRes.stores : localStores());
      setLoaded(true);
    })();
    return () => { alive = false; };
  }, []);

  const points = useMemo(() => cityPointsFrom(stores), [stores]);

  /* 城市卡片：按 city 聚合门店，坐标取该城市点位均值 */
  const cityCards = useMemo(() => {
    const group = new Map();
    stores.forEach((s) => {
      if (!s.city) return;
      if (!group.has(s.city)) group.set(s.city, []);
      group.get(s.city).push(s);
    });
    return Array.from(group.entries()).map(([city, list]) => {
      const pt = points.find((p) => p.city === city) || {};
      return { city, lng: pt.lng, lat: pt.lat, count: list.length, stores: list };
    });
  }, [stores, points]);

  const matches = useMemo(() => {
    const q = search.trim();
    return cityCards.filter((c) => !q || c.city.includes(q));
  }, [cityCards, search]);

  /* ---------- 地图初始化（与门店地图页共用单例加载器；无 Key / 离线时显示兜底错误层） ---------- */
  useEffect(() => {
    let cancelled = false;
    let intervalId, stopId;
    const showError = () => {
      if (loadingRef.current) loadingRef.current.style.display = "none";
      if (errorRef.current) errorRef.current.style.display = "flex";
    };
    const init = () => {
      if (mapRef.current) return; // 防止 StrictMode 下重复初始化
      if (typeof window.TMap === "undefined") { showError(); return; }
      try {
        const T = window.TMap;
        const map = new T.Map("storeMap", {
          center: new T.LatLng(34.5, 108.5),
          zoom: 4.4, minZoom: 3, maxZoom: 12,
          baseMap: { type: "vector", features: ["base", "building3d"] },
        });
        mapRef.current = map;
        markersRef.current = new T.MultiMarker({
          map,
          styles: { pin: new T.MarkerStyle({ width: 30, height: 38, anchor: { x: 15, y: 38 }, src: PIN_URL }) },
          geometries: [],
        });
        map.on("click", () => infoRef.current && infoRef.current.close());
        const info = new T.InfoWindow({ map, position: new T.LatLng(34.5, 108.5), offset: { x: 0, y: -32 }, content: '<div class="iw"></div>' });
        info.close();
        infoRef.current = info;
        map.on("tilesloaded", () => { if (loadingRef.current) loadingRef.current.style.display = "none"; });
        setTimeout(() => { if (loadingRef.current) loadingRef.current.style.display = "none"; }, 2500);
        // 首帧之后布局才稳定（字体 / 图片回流）的情况，再补一次尺寸重算
        setTimeout(() => { try { if (map.resize) map.resize(); } catch (e) { /* noop */ } }, 300);
        setMapReady(true); // 通知点位挂载；地图晚于数据就绪时也不会漏挂
      } catch (err) {
        showError();
      }
    };

    // 兼容清理腾讯地图「鉴权失败」提示条：只删「只包含这句提示」的最小元素，绝不碰地图容器
    const removeAuthBanners = () => {
      if (typeof document === "undefined" || !document.body) return; // 页面销毁后回调可能仍会触发
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
      const targets = new Set();
      let t;
      while ((t = walker.nextNode())) {
        if (!t.nodeValue || !t.nodeValue.includes("鉴权失败")) continue;
        let el = t.parentElement;
        let guard = 0;
        while (el && guard < 4) {
          const isMap = el.id === "storeMap" || (el.classList && el.classList.contains("store-map"));
          if (isMap) break; // 守住地图容器，绝不删除
          const txt = (el.textContent || "").trim();
          if (txt.length <= 120) { targets.add(el); break; }
          el = el.parentElement;
          guard++;
        }
      }
      targets.forEach(el => el.remove());
    };
    const observer = new MutationObserver(() => removeAuthBanners());
    observer.observe(document.body, { childList: true, subtree: true });
    intervalId = setInterval(removeAuthBanners, 1500);
    stopId = setTimeout(() => { observer.disconnect(); clearInterval(intervalId); }, 12000);

    if (!TMAP_KEY) { showError(); }
    else {
      // 已加载则立即复用（与 /stores 往返切换时不会重复注入脚本）
      loadTMap(TMAP_KEY)
        .then(async () => {
          if (cancelled || mapRef.current) return;
          await waitForLayout(document.getElementById("storeMap"));
          if (cancelled) return;
          init();
          removeAuthBanners();
          setTimeout(removeAuthBanners, 1200);
        })
        .catch(showError);
    }

    return () => {
      cancelled = true;
      clearTimeout(stopId);
      clearInterval(intervalId);
      observer.disconnect();
      // 注意：不卸载已加载的全局 SDK（window.TMap），只清理本组件的副作用
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* 容器尺寸变化后 GL 地图不会自动重算视口 */
  useEffect(() => {
    return observeResize(document.getElementById("storeMap"), () => {
      try {
        if (mapRef.current && typeof mapRef.current.resize === "function") mapRef.current.resize();
      } catch (e) { /* noop */ }
    });
  }, []);

  /* 点位随数据更新：门店数据异步到达，地图也可能后到 —— mapReady 变化时重挂，确保不漏 */
  useEffect(() => {
    if (!mapReady || !mapRef.current || !markersRef.current || !window.TMap) return;
    const mk = markersRef.current;
    mk.setGeometries(
      points.map((p) => ({ id: p.city, styleId: "pin", position: new window.TMap.LatLng(p.lat, p.lng), properties: { city: p.city } }))
    );
    const handler = (e) => { if (openCityRef.current) openCityRef.current(e.geometry.properties.city, false); };
    mk.on("click", handler);
    return () => { try { mk.off && mk.off("click", handler); } catch (e) { /* 旧版 SDK 可能无 off */ } };
  }, [mapReady, points]);

  const openCity = (name, fly) => {
    const c = cityCards.find((x) => x.city === name);
    if (!c) return;
    setActiveCity(name);
    if (mapRef.current && fly && window.TMap && c.lng != null) {
      mapRef.current.easeTo({ center: new window.TMap.LatLng(c.lat, c.lng), zoom: 8, duration: 600 });
    }
    if (infoRef.current && c.lng != null) {
      const lis = c.stores.map(s => `<li>${s.name} · ${s.addr}</li>`).join("");
      infoRef.current.setPosition(new window.TMap.LatLng(c.lat, c.lng));
      infoRef.current.setContent(`<div class="iw"><b>${c.city}</b><div class="sub">${c.count} 家门店</div><ul>${lis}</ul><a class="more" href="/stores">查看详情</a></div>`);
      infoRef.current.open();
    }
  };
  openCityRef.current = openCity;

  return (
    <section className="store-entry" id="stores">
      <div className="wrap store-inner">
        <div className="store-copy">
          <div className="eyebrow" style={{ marginBottom: 18 }}>门店</div>
          <div className="big">全国 <em>{cityCards.length}</em> 城 <em>{stores.length}</em> 家门店<br />让「看到」变为「找到」</div>
          <p>全国门店地图 + 城市筛选 + 列表同页联动（PRD F4）。点击进入可查看具体地址、营业时间与今日营业状态。</p>
          <div style={{ display: "flex", gap: 14, marginTop: 30 }}>
            <Link className="btn" to="/stores">查看门店地图
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
            </Link>
            <Link className="btn ghost" to="/stores">查询附近门店</Link>
          </div>
        </div>

        <div className="store-map" aria-label="中国门店分布地图">
          <div id="storeMap" role="application" aria-label="中国地图，标注各城市门店位置"></div>
          <div className="map-hint">点击城市标记查看门店 · 拖拽平移 / 滚轮缩放</div>
          <div className="map-loading" ref={loadingRef}><div className="spin"></div><div>正在加载中国底图…</div></div>
          <div className="map-error" ref={errorRef}><b>底图加载失败</b><div>当前为本地开发模式；若需地图，请在 window.__FLY_TMAP_KEY__ 配置腾讯位置服务 Key。</div></div>
          <div className={`store-cities${search ? " searching" : ""}`}>
            <div className="city-search">
              <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7" /><path d="M20 20 L16.5 16.5" /></svg>
              <input type="search" placeholder="搜索城市，如 上海" aria-label="搜索城市" value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <div className="city-list" role="listbox" aria-label="城市门店列表">
              {matches.map(c => (
                <div className={`city-item${activeCity === c.city ? " active" : ""}`} key={c.city} role="option" tabIndex={0}
                  aria-label={`${c.city}，${c.count} 家门店`} onClick={() => openCity(c.city, true)}
                  onKeyDown={e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openCity(c.city, true); } }}>
                  <span className="pin"></span>
                  <div className="meta"><b>{c.city}</b><span>{c.stores[0].name} 等 {c.count} 家</span></div>
                  <span className="badge">{c.count}</span>
                </div>
              ))}
              {loaded && !matches.length && (
                <div className="city-item" aria-disabled="true"><div className="meta"><span>暂无匹配城市</span></div></div>
              )}
            </div>
            <div className="city-hint" aria-hidden="true">{matches.length ? `共 ${matches.length} 条结果 · 下拉滚动查看更多` : ""}</div>
          </div>
        </div>
      </div>
    </section>
  );
}
