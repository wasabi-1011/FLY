// 门店域前台取数层：优先读后端 /api/stores/*（公开只读，无需登录）。
// 约定与 newsApi / productsApi 完全一致：
//   - 接口成功但列表为空 → 后台真的把门店全下线/删光了 → 前台显示空状态，不回退默认。
//   - 接口失败（后端未启动 / 网络错误 / 5xx）→ 才回退本地 siteData 示例，保证官网不白屏。
//
// 坐标：后端 stores.lng/lat 与腾讯底图同为 GCJ-02，前端直接用来打点，**不做任何坐标转换**。
import { STORE_CITIES, STORE_TOTAL } from "./siteData.js";

const TYPE_TEXT = { FLAGSHIP: "旗舰店", STANDARD: "标准店", OUTLET: "奥莱店" };

/** 后端 Store → 前台门店条目 */
export function toStore(s) {
  return {
    id: s.id,
    name: s.name,
    province: s.province || "",
    city: s.city || "",
    district: s.district || "",
    addr: s.address || "",
    phone: s.phone || "",
    hours: s.business_hours || "",
    type: s.store_type || "STANDARD",
    typeText: TYPE_TEXT[s.store_type] || "标准店",
    img: (s.images && s.images[0]) || "",
    lng: s.lng,
    lat: s.lat,
  };
}

async function getJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error("HTTP " + r.status);
  return r.json();
}

/**
 * 门店列表（只返回 status=online 的门店，由后端过滤）。
 * @returns {Promise<{ok: boolean, stores: Array|null}>} ok=false 时调用方回退本地数据。
 */
export async function fetchStores() {
  try {
    const d = await getJSON("/api/stores");
    return { ok: true, stores: (d || []).map(toStore) }; // 空数组也算 ok
  } catch {
    return { ok: false, stores: null };
  }
}

/** 有门店的城市 + 门店数（供城市 chips 初始化） */
export async function fetchStoreCities() {
  try {
    const d = await getJSON("/api/stores/cities");
    return {
      ok: true,
      cities: (d || []).map((c) => ({ city: c.city, count: c.store_count })),
    };
  } catch {
    return { ok: false, cities: null };
  }
}

/** 门店详情（PRD FR-F34：独立可收录 URL 的数据来源） */
export async function fetchStore(id) {
  try {
    const d = await getJSON(`/api/stores/${encodeURIComponent(id)}`);
    return { ok: true, store: toStore(d) };
  } catch {
    return { ok: false, store: null };
  }
}

/* ---------- 本地默认数据（仅作「后端不可用」时的兜底） ---------- */

export const localCities = () =>
  (STORE_CITIES || []).map((c) => ({ city: c.name, count: (c.stores || []).length }));

export const localStores = () => {
  const out = [];
  (STORE_CITIES || []).forEach((c) => {
    (c.stores || []).forEach((s) =>
      out.push({
        id: null,
        name: s.n,
        province: "",
        city: c.name,
        district: "",
        addr: s.a,
        phone: "",
        hours: "10:00 - 22:00",
        type: "STANDARD",
        typeText: "标准店",
        img: "",
        lng: c.lng,
        lat: c.lat,
      })
    );
  });
  return out;
};

export const localStoreTotal = () => STORE_TOTAL;

/** 按城市聚合出地图点位（取该城市门店坐标的均值） */
export function cityPointsFrom(stores) {
  const map = new Map();
  stores.forEach((s) => {
    if (s.lng == null || s.lat == null) return;
    const g = map.get(s.city) || { city: s.city, lng: 0, lat: 0, n: 0 };
    g.lng += s.lng; g.lat += s.lat; g.n += 1;
    map.set(s.city, g);
  });
  return Array.from(map.values()).map((g) => ({
    city: g.city,
    lng: g.lng / g.n,
    lat: g.lat / g.n,
    count: g.n,
  }));
}
