// 商品域（款式 / 系列）前台取数层：优先读后端 /api/products/*；
// 仅在「接口不可用」时回退本地 siteData（与 newsApi 的约定完全一致）。
//
// 关键约定（区分「空」与「失败」）：
//   - 接口请求成功但列表为空 → 后台真的把款式下架或删光了 → 前台显示空状态，不回退默认。
//   - 接口请求失败（网络错误 / 后端未启动 / 5xx）→ 才回退本地示例数据，保证官网不白屏。
//
// 层级（v2.2 起）：品类 → 款式 → 系列。
//   后端一个 item 已自带其 series 列表（选填），前端不再需要按系列对象分组。
//
// 字段映射（后端 → 前台）：item_code → code、images[] → img、is_hot → hot、
// category → cat、series[] → series；页面组件无需感知后端字段名。
import {
  getItemsByCat,
  getAllItems,
  getHotItems,
  findItem,
  getRelatedItems,
} from "./siteData.js";

const SEASON_TEXT = { SPRING_SUMMER: "春夏", AUTUMN_WINTER: "秋冬", CAPSULE: "胶囊" };
const CAT_LIST = ["men", "women", "kids"];

/** 系列展示用季节文案：2026 + AUTUMN_WINTER → “2026 秋冬” */
export function seasonLabel(year, season) {
  const s = SEASON_TEXT[season] || "";
  if (year && s) return `${year} ${s}`;
  return s || (year ? String(year) : "");
}

const fallbackImg = (cat) => `/pic/series-${cat}.jpg`;

/** 后端 Collection → 前台系列条目（挂在款式上） */
export function toSeries(s, cat) {
  return {
    id: s.id,
    name: s.name,
    season: seasonLabel(s.year, s.season),
    cover: s.cover_image || fallbackImg(cat),
  };
}

/** 后端 Item → 前台款式卡片 */
export function toItem(it) {
  const cat = it.category;
  return {
    id: it.id,
    code: it.item_code,
    name: it.name,
    hot: !!it.is_hot,
    img: (it.images && it.images[0]) || fallbackImg(cat),
    // desc 用作卡片摘要与详情页导语 → 取设计说明；fit 单独成字段，避免与导语重复
    desc: it.description || it.fit_description || "",
    fit: it.fit_description || "",
    // 后端无独立「品牌故事」字段，留空不渲染（故事仅在本地兜底数据里存在）
    story: "",
    fabric: it.fabric || "",
    points: [],
    care: "",
    cat,
    series: (it.series || []).map((s) => toSeries(s, cat)),
  };
}

async function getJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error("HTTP " + r.status);
  return r.json();
}

/**
 * 品类页数据：该品类下的全部在线款式（每个款式自带其系列）。
 * @returns {Promise<{ok: boolean, items: Array|null}>} ok=false 表示接口不可用，调用方应回退本地。
 */
export async function fetchCategoryPage(cat) {
  try {
    const d = await getJSON(`/api/products/${encodeURIComponent(cat)}`);
    return { ok: true, items: (d.items || []).map(toItem) }; // 空数组也算 ok
  } catch {
    return { ok: false, items: null };
  }
}

/**
 * 全站热门（is_hot 人工标记，服务端已按 hot_sort 排序）。
 * @returns {Promise<{ok: boolean, items: Array|null}>}
 */
export async function fetchHotItems() {
  try {
    const d = await getJSON("/api/products/hot");
    const arr = Array.isArray(d) ? d : d.items || [];
    return { ok: true, items: arr.map(toItem) };
  } catch {
    return { ok: false, items: null };
  }
}

/**
 * 产品中心「全系列款式」：并发取三个品类。
 * 只要有一个品类成功就算 ok（部分品类异常不至于整页回退演示数据）。
 * @returns {Promise<{ok: boolean, items: Array|null}>}
 */
export async function fetchAllItems() {
  const results = await Promise.all(CAT_LIST.map((c) => fetchCategoryPage(c)));
  if (results.every((r) => !r.ok)) return { ok: false, items: null };
  const items = [];
  results.forEach((r) => {
    if (r.ok) items.push(...r.items);
  });
  return { ok: true, items };
}

/**
 * 单品详情：按「品类 + 款号」在品类数据里定位（款式自带系列）。
 * @returns {Promise<{ok: boolean, found: object|null, items: Array|null}>}
 *   ok=true 且 found=null → 后端确认该款不存在或已下架（调用方跳回产品中心，不回退本地）。
 *   ok=false → 接口不可用，调用方回退本地示例。
 *   items：该品类全部款式，供详情页「相关推荐」复用，避免二次请求。
 */
export async function fetchItemDetail(cat, code) {
  const res = await fetchCategoryPage(cat);
  if (!res.ok) return { ok: false, found: null, items: null };
  const item = res.items.find((x) => x.code === code);
  return { ok: true, found: item ? { item } : null, items: res.items };
}

/* ---------- 本地默认数据（仅作「后端不可用」时的兜底） ---------- */

/**
 * 本地款式已自带 series 数组（与接口出参同构），这里只补齐缺省字段：
 * id 缺省 null、season 缺省空串、cover 缺省按品类兜底。
 */
const asLocal = (list) =>
  list.map((i) => ({
    ...i,
    series: (i.series || []).map((s) => ({
      id: s.id ?? null,
      name: s.name,
      season: s.season || "",
      cover: s.cover || fallbackImg(i.cat),
    })),
  }));

export const localItemsByCat = (cat) => asLocal(getItemsByCat(cat));
export const localAllItems = () => asLocal(getAllItems());
// 本地热门按 HOT_ORDER 排序（与后端 hot_sort 同序），不用 filter(hot) 以免顺序漂移
export const localHotItems = () => asLocal(getHotItems());
export const localFindItem = (cat, code) => {
  const l = findItem(cat, code);
  return l ? { item: asLocal([l.item])[0] } : null;
};
export const localRelated = (cat, code) => getRelatedItems(cat, code);

/** 详情页相关推荐：同品类排除当前款，同系列优先（与本地实现保持一致） */
export function relatedFrom(items, cat, code) {
  const all = items.filter((i) => i.cat === cat);
  const cur = all.find((i) => i.code === code);
  const others = all.filter((i) => i.code !== code);
  const curSeries = (cur && cur.series && cur.series[0] && cur.series[0].name) || null;
  const sameSeries = curSeries
    ? others.filter((i) => i.series && i.series[0] && i.series[0].name === curSeries)
    : [];
  const rest = others.filter((i) => !sameSeries.includes(i));
  return [...sameSeries, ...rest].slice(0, 3);
}
