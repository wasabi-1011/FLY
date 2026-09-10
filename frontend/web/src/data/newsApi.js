// 新闻数据接入层：优先读后端 /api/news；仅在「接口不可用」时回退本地 siteData。
//
// 关键约定（区分「空」与「失败」）：
//   - 接口请求成功但列表为空 → 说明后台真的把内容删光了 → 前台显示空状态，不回退默认。
//   - 接口请求失败（网络错误 / 后端未启动 / 5xx）→ 才回退本地默认内容，保证官网不白屏。
import { NEWS } from "./siteData.js";

export const FALLBACK_COVER = {
  company: "/pic/news-01.jpg",
  industry: "/pic/news-03.jpg",
};

// 后端 Article → 前台卡片结构（与 siteData.NEWS 字段对齐）
export const toCard = (a) => ({
  cat: a.category,
  slug: a.slug,
  title: a.title,
  cover: a.cover_image || FALLBACK_COVER[a.category] || "/pic/news-01.jpg",
  lead: a.summary || "",
  date: (a.published_at || "").slice(0, 10) || "2026-09-01",
  place: a.place || "",
  editor: a.author || "FLY 品牌部",
  html: a.content || "", // 后端已做 XSS 白名单过滤
});

/* ---------- 本地默认数据（仅作「后端不可用」时的兜底） ---------- */
export const localList = (cat) => NEWS.filter((n) => n.cat === cat);
export const localDetail = (cat, slug) =>
  NEWS.find((n) => n.cat === cat && n.slug === slug) || null;
export const localLatest = (n) => NEWS.slice(0, n);

async function getJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error("HTTP " + r.status);
  return r.json();
}

/**
 * 新闻列表。
 * @returns {Promise<{ok: boolean, items: Array|null}>} ok=false 表示接口不可用，调用方应回退本地。
 */
export async function fetchNewsList(cat) {
  try {
    const d = await getJSON(
      `/api/news?category=${encodeURIComponent(cat)}&page_size=50`
    );
    const items = Array.isArray(d) ? d : d.items || [];
    return { ok: true, items: items.map(toCard) }; // 注意：空数组也算 ok
  } catch {
    return { ok: false, items: null };
  }
}

/**
 * 最新新闻（跨分类，供首页使用）。
 * @returns {Promise<{ok: boolean, items: Array|null}>}
 */
export async function fetchLatestNews(limit = 3) {
  try {
    const d = await getJSON(`/api/news?page_size=${limit}`);
    const items = Array.isArray(d) ? d : d.items || [];
    return { ok: true, items: items.slice(0, limit).map(toCard) };
  } catch {
    return { ok: false, items: null };
  }
}

/**
 * 新闻详情。
 * @returns {Promise<{ok: boolean, article: object|null}>}
 *   ok=true 且 article=null → 后端确认该文不存在或未发布（不应回退本地）。
 *   ok=false → 接口不可用，调用方回退本地默认。
 */
export async function fetchNewsDetail(cat, slug) {
  try {
    const r = await fetch(
      `/api/news/${encodeURIComponent(cat)}/${encodeURIComponent(slug)}`
    );
    if (r.status === 404) return { ok: true, article: null };
    if (!r.ok) throw new Error("HTTP " + r.status);
    const d = await r.json();
    return { ok: true, article: d && d.slug ? toCard(d) : null };
  } catch {
    return { ok: false, article: null };
  }
}
