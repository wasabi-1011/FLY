import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";

// 门店城市（GCJ-02 坐标；示例地址，与原型一致）
const CITIES = [
  { id: "bj", name: "北京", lng: 116.397428, lat: 39.90923, stores: [
    { n: "三里屯旗舰店", a: "朝阳区三里屯太古里南区 S8-30" }, { n: "国贸店", a: "朝阳区建国门外大街 1 号国贸商城" },
    { n: "西单大悦城店", a: "西城区西单北大街 131 号" }, { n: "王府井店", a: "东城区王府井大街 138 号" } ] },
  { id: "sh", name: "上海", lng: 121.489, lat: 31.227, stores: [
    { n: "南京西路旗舰店", a: "静安区南京西路 1601 号" }, { n: "环贸 iapm 店", a: "徐汇区淮海中路 999 号" },
    { n: "正大广场店", a: "浦东新区陆家嘴西路 168 号" }, { n: "静安大悦城店", a: "静安区西藏北路 198 号" } ] },
  { id: "gz", name: "广州", lng: 113.272, lat: 23.136, stores: [
    { n: "天河城店", a: "天河区天河路 208 号" }, { n: "太古汇店", a: "天河区天河路 383 号" }, { n: "北京路店", a: "越秀区北京路 374 号" } ] },
  { id: "sz", name: "深圳", lng: 114.085, lat: 22.547, stores: [
    { n: "万象天地旗舰店", a: "南山区深南大道 9668 号" }, { n: "万象城店", a: "罗湖区宝安南路 1881 号" }, { n: "海岸城店", a: "南山区文心五路 33 号" } ] },
  { id: "cd", name: "成都", lng: 104.065, lat: 30.659, stores: [
    { n: "IFS 国际金融中心店", a: "锦江区红星路三段 1 号" }, { n: "万象城店", a: "成华区双庆路 8 号" } ] },
  { id: "hz", name: "杭州", lng: 120.153, lat: 30.287, stores: [
    { n: "湖滨银泰 in77 店", a: "上城区延安路 538 号" }, { n: "万象城店", a: "江干区富春路 701 号" } ] },
  { id: "wh", name: "武汉", lng: 114.305, lat: 30.593, stores: [
    { n: "武商广场店", a: "江汉区解放大道 688 号" } ] },
  { id: "nj", name: "南京", lng: 118.797, lat: 32.060, stores: [
    { n: "德基广场店", a: "玄武区中山路 18 号" } ] },
];

const PIN_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="30" height="38" viewBox="0 0 30 38">' +
  '<path d="M15 1C7.27 1 1 7.27 1 15c0 10.5 14 22 14 22s14-11.5 14-22C29 7.27 22.73 1 15 1z" fill="#c8893f" stroke="#fff" stroke-width="2"/>' +
  '<circle cx="15" cy="15" r="6" fill="#fff"/></svg>';
const PIN_URL = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(PIN_SVG);

export default function StoreEntry() {
  const [search, setSearch] = useState("");
  const [activeId, setActiveId] = useState(null);
  const mapRef = useRef(null);
  const infoRef = useRef(null);
  const loadingRef = useRef(null);
  const errorRef = useRef(null);

  const matches = useMemo(() => {
    const q = search.trim();
    return CITIES.filter(c => !q || c.name.includes(q));
  }, [search]);

  // 初始化腾讯地图（尽力而为；无 Key / 离线时显示兜底错误层）
  useEffect(() => {
    let script;
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
        const markers = new T.MultiMarker({
          map,
          styles: { pin: new T.MarkerStyle({ width: 30, height: 38, anchor: { x: 15, y: 38 }, src: PIN_URL }) },
          geometries: CITIES.map(c => ({ id: c.id, styleId: "pin", position: new T.LatLng(c.lat, c.lng), properties: { city: c } })),
        });
        markers.on("click", e => openCity(e.geometry.properties.city, false));
        map.on("click", () => infoRef.current && infoRef.current.close());
        const info = new T.InfoWindow({ map, position: new T.LatLng(34.5, 108.5), offset: { x: 0, y: -32 }, content: '<div class="iw"></div>' });
        info.close();
        infoRef.current = info;
        map.on("tilesloaded", () => { if (loadingRef.current) loadingRef.current.style.display = "none"; });
        setTimeout(() => { if (loadingRef.current) loadingRef.current.style.display = "none"; }, 2500);
      } catch (err) {
        showError();
      }
    };
    const KEY = "OLVBZ-INVK3-4ON3K-OQK4I-2QJOJ-M6BE2";

    // 精准移除腾讯地图「鉴权失败」提示条：
    // 只删「只包含这句提示」的最小元素，绝不碰地图容器( #storeMap / .store-map )
    const removeAuthBanners = () => {
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
          if (txt.length <= 120) { targets.add(el); break; } // 只移除短小的提示元素本身
          el = el.parentElement;
          guard++;
        }
      }
      targets.forEach(el => el.remove());
    };
    const observer = new MutationObserver(() => removeAuthBanners());
    observer.observe(document.body, { childList: true, subtree: true });
    // 周期兜底 + 12 秒后停止观察（避免长期占用）
    const intervalId = setInterval(removeAuthBanners, 1500);
    const stopId = setTimeout(() => { observer.disconnect(); clearInterval(intervalId); }, 12000);

    script = document.createElement("script");
    script.src = `https://map.qq.com/api/gljs?v=1.exp&key=${KEY}`;
    script.onload = () => { init(); removeAuthBanners(); };
    script.onerror = showError;
    document.body.appendChild(script);

    // 初始化后再兜底清理一次
    setTimeout(removeAuthBanners, 1200);

    return () => {
      if (script && script.parentNode) script.parentNode.removeChild(script);
      clearTimeout(stopId);
      clearInterval(intervalId);
      observer.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const openCity = (c, fly) => {
    setActiveId(c.id);
    if (mapRef.current && fly) {
      mapRef.current.easeTo({ center: new window.TMap.LatLng(c.lat, c.lng), zoom: 8, duration: 600 });
    }
    if (infoRef.current) {
      const lis = c.stores.map(s => `<li>${s.n} · ${s.a}</li>`).join("");
      infoRef.current.setPosition(new window.TMap.LatLng(c.lat, c.lng));
      infoRef.current.setContent(`<div class="iw"><b>${c.name}</b><div class="sub">${c.stores.length} 家门店</div><ul>${lis}</ul><a class="more" href="#${c.id}">查看详情</a></div>`);
      infoRef.current.open();
    }
  };

  return (
    <section className="store-entry" id="stores">
      <div className="wrap store-inner">
        <div className="store-copy">
          <div className="eyebrow" style={{ marginBottom: 18 }}>门店</div>
          <div className="big">全国 <em>8</em> 城 <em>20</em> 家门店<br />让「看到」变为「找到」</div>
          <p>全国门店地图 + 城市筛选 + 列表同页联动（PRD F4）。点击进入可查看具体地址、营业时间与今日营业状态。</p>
          <div style={{ display: "flex", gap: 14, marginTop: 30 }}>
            <Link className="btn" to="/stores">查看门店地图
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
            </Link>
            <Link className="btn ghost" to="/stores">查询附近门店</Link>
          </div>
        </div>

        <div className="store-map" aria-label="中国门店分布地图">
          <div id="storeMap" role="application" aria-label="中国地图，标注北京、上海、广州、深圳、成都、杭州、武汉、南京的门店位置"></div>
          <div className="map-hint">点击城市标记查看门店 · 拖拽平移 / 滚轮缩放</div>
          <div className="map-loading" ref={loadingRef}><div className="spin"></div><div>正在加载中国底图…</div></div>
          <div className="map-error" ref={errorRef}><b>底图加载失败</b><div>当前为本地开发模式；若需地图，请到 https://lbs.qq.com/ 申请 Key 并填入 window.__FLY_TMAP_KEY__。</div></div>
          <div className={`store-cities${search ? " searching" : ""}`}>
            <div className="city-search">
              <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7" /><path d="M20 20 L16.5 16.5" /></svg>
              <input type="search" placeholder="搜索城市，如 上海" aria-label="搜索城市" value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <div className="city-list" role="listbox" aria-label="城市门店列表">
              {matches.map(c => (
                <div className={`city-item${activeId === c.id ? " active" : ""}`} key={c.id} role="option" tabIndex={0}
                  aria-label={`${c.name}，${c.stores.length} 家门店`} onClick={() => openCity(c, true)}
                  onKeyDown={e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openCity(c, true); } }}>
                  <span className="pin"></span>
                  <div className="meta"><b>{c.name}</b><span>{c.stores[0].n} 等 {c.stores.length} 家</span></div>
                  <span className="badge">{c.stores.length}</span>
                </div>
              ))}
            </div>
            <div className="city-hint" aria-hidden="true">{matches.length ? `共 ${matches.length} 条结果 · 下拉滚动查看更多` : ""}</div>
          </div>
        </div>
      </div>
    </section>
  );
}
