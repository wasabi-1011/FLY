import { useEffect, useMemo, useRef, useState } from "react";
import SiteNav from "../components/SiteNav.jsx";
import SiteFooter from "../components/SiteFooter.jsx";
import PageHero from "../components/PageHero.jsx";
import { STORE_CITIES, STORE_TOTAL } from "../data/siteData.js";

const TMAP_KEY = "OLVBZ-INVK3-4ON3K-OQK4I-2QJOJ-M6BE2";

const PIN_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="30" height="38" viewBox="0 0 30 38">' +
  '<path d="M15 1C7.27 1 1 7.27 1 15c0 10.5 14 22 14 22s14-11.5 14-22C29 7.27 22.73 1 15 1z" fill="#c8893f" stroke="#fff" stroke-width="2"/>' +
  '<circle cx="15" cy="15" r="6" fill="#fff"/></svg>';
const PIN_URL = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(PIN_SVG);

export default function Stores() {
  const [city, setCity] = useState("all"); // 'all' | city id
  const mapRef = useRef(null);
  const iwRef = useRef(null);
  const statusRef = useRef(null); // 地图加载/错误提示区

  const curCity = city === "all" ? null : STORE_CITIES.find(c => c.id === city);

  const cityCount = useMemo(() => STORE_CITIES.length, []);
  useEffect(() => { document.title = "门店查询 · FLY"; }, []);

  // ---- 腾讯地图初始化（对齐首页 StoreEntry 的做法） ----
  useEffect(() => {
    let script;
    const say = (state) => { if (statusRef.current) statusRef.current.dataset.state = state; };

    const removeAuthBanners = () => {
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
      const targets = new Set();
      let t;
      while ((t = walker.nextNode())) {
        if (!t.nodeValue || !t.nodeValue.includes("鉴权失败")) continue;
        let el = t.parentElement, guard = 0;
        while (el && guard < 4) {
          if (el.id === "storeMap" || (el.classList && el.classList.contains("store-map"))) break;
          const txt = (el.textContent || "").trim();
          if (txt.length <= 120) { targets.add(el); break; }
          el = el.parentElement; guard++;
        }
      }
      targets.forEach(el => el.remove());
    };
    const observer = new MutationObserver(() => removeAuthBanners());
    observer.observe(document.body, { childList: true, subtree: true });
    const intervalId = setInterval(removeAuthBanners, 1500);
    const stopId = setTimeout(() => { observer.disconnect(); clearInterval(intervalId); }, 12000);

    const init = () => {
      if (mapRef.current || typeof window.TMap === "undefined") return;
      try {
        const T = window.TMap;
        const map = new T.Map("storeMap", {
          center: new T.LatLng(34.5, 108.5), zoom: 4.4, minZoom: 3, maxZoom: 12,
          baseMap: { type: "vector", features: ["base", "building3d"] },
        });
        mapRef.current = map;
        const markers = new T.MultiMarker({
          map,
          styles: { pin: new T.MarkerStyle({ width: 30, height: 38, anchor: { x: 15, y: 38 }, src: PIN_URL }) },
          geometries: STORE_CITIES.map(c => ({ id: c.id, styleId: "pin", position: new T.LatLng(c.lat, c.lng) })),
        });
        markers.on("click", e => openCity(e.geometry.id));
        map.on("click", () => iwRef.current && iwRef.current.close());
        const iw = new T.InfoWindow({ map, position: new T.LatLng(34.5, 108.5), offset: { x: 0, y: -32 }, content: '<div class="iw"></div>' });
        iw.close(); iwRef.current = iw;
        map.on("tilesloaded", () => say("ready"));
        setTimeout(() => say("ready"), 2500);
        say("loading");
      } catch (e) { say("error"); }
    };

    const openCity = (id) => {
      const c = STORE_CITIES.find(x => x.id === id); if (!c) return;
      setCity(id);
      if (mapRef.current && window.TMap) {
        mapRef.current.easeTo({ center: new window.TMap.LatLng(c.lat, c.lng), zoom: 7.5, duration: 600 });
        const lis = c.stores.map(s => `<li>${s.n} · ${s.a}</li>`).join("");
        const info = iwRef.current;
        if (info) {
          info.setPosition(new window.TMap.LatLng(c.lat, c.lng));
          info.setContent(`<div class="iw"><b>${c.name}</b><div class="sub">${c.stores.length} 家门店</div><ul>${lis}</ul></div>`);
          info.open();
        }
      }
    };

    script = document.createElement("script");
    script.src = `https://map.qq.com/api/gljs?v=1.exp&key=${TMAP_KEY}`;
    script.onload = () => { init(); removeAuthBanners(); };
    script.onerror = () => say("error");
    document.body.appendChild(script);
    setTimeout(removeAuthBanners, 1200);

    return () => {
      if (script && script.parentNode) script.parentNode.removeChild(script);
      clearTimeout(stopId); clearInterval(intervalId); observer.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const flyTo = (id) => {
    setCity(id);
    const c = STORE_CITIES.find(x => x.id === id); if (!c || !mapRef.current || !window.TMap) return;
    mapRef.current.easeTo({ center: new window.TMap.LatLng(c.lat, c.lng), zoom: 9.5, duration: 600 });
    const lis = c.stores.map(s => `<li>${s.n} · ${s.a}</li>`).join("");
    const info = iwRef.current;
    if (info) {
      info.setPosition(new window.TMap.LatLng(c.lat, c.lng));
      info.setContent(`<div class="iw"><b>${c.name}</b><div class="sub">${c.stores.length} 家门店 · 营业时间 10:00–22:00</div><ul>${lis}</ul></div>`);
      info.open();
    }
  };

  const resetAll = () => {
    setCity("all");
    if (mapRef.current && window.TMap) {
      mapRef.current.easeTo({ center: new window.TMap.LatLng(34.5, 108.5), zoom: 4.4, duration: 600 });
      if (iwRef.current) iwRef.current.close();
    }
  };

  // 列表数据：全部城市平铺 / 选中城市
  const rows = curCity
    ? curCity.stores.map(s => ({ ...s, cityId: curCity.id, city: curCity.name }))
    : STORE_CITIES.flatMap(c => c.stores.map(s => ({ ...s, cityId: c.id, city: c.name })));

  return (
    <>
      <SiteNav />
      <div className="sub-page stores-page">
        <PageHero
          crumbs={[{ label: "门店" }]}
          title="门店地图"
          en="STORES"
          sub={`全国 ${cityCount} 城 ${STORE_TOTAL} 家门店 · 点选城市或图钉查看门店`}
          bg="/pic/storefront-01.jpg"
        />

        {/* 城市联动 chips */}
        <div className="wrap">
          <div className="store-chips" role="tablist" aria-label="按城市筛选门店">
            <button role="tab" aria-selected={city === "all"} className={`chip${city === "all" ? " on" : ""}`}
              onClick={resetAll}>全部 · {STORE_TOTAL}</button>
            {STORE_CITIES.map(c => (
              <button role="tab" aria-selected={city === c.id} className={`chip${city === c.id ? " on" : ""}`}
                key={c.id} onClick={() => flyTo(c.id)}>{c.name} · {c.stores.length}</button>
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
              <div className="st-err"><b>底图加载失败</b><div>当前为本地开发模式；请确认腾讯地图 Key 已配置且网络可用。门店列表仍可正常浏览。</div></div>
            </div>
          </div>
        </div>

        {/* 门店列表 */}
        <section className="wrap">
          <div className="sec-head" style={{ marginTop: 8 }}>
            <div>
              <div className="eyebrow" style={{ marginBottom: 10 }}>{curCity ? `当前城市 · ${curCity.name}` : "全部城市"}</div>
              <h2 className="sec-title">{curCity ? curCity.name : "全部门店"} <small className="count">共 {rows.length} 家</small></h2>
            </div>
            {curCity && <button className="chip" onClick={resetAll}>显示全部城市</button>}
          </div>
          <div className="store-grid">
            {rows.map((s, i) => (
              <button className="store-card" key={i} onClick={() => flyTo(s.cityId)}>
                <span className="badge">{s.city}</span>
                <b>{s.n}</b>
                <span className="addr">{s.a}</span>
                <span className="hours">营业时间 10:00 – 22:00</span>
                <span className="goto">地图定位 →</span>
              </button>
            ))}
          </div>
        </section>
      </div>
      <SiteFooter />
    </>
  );
}
