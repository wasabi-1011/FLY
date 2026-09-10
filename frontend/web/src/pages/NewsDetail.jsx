import { useEffect, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import SiteNav from "../components/SiteNav.jsx";
import SiteFooter from "../components/SiteFooter.jsx";
import { formatDate } from "../data/siteData.js";
import { fetchNewsDetail, fetchNewsList, localDetail, localList } from "../data/newsApi.js";

const CAT_LABEL = { company: "企业新闻", industry: "行业资讯" };

// 正文节点渲染：lead/p/h/quote/img（仅当后端未返回 HTML 时使用，例如本地兜底数据）
function Body({ nodes }) {
  return (
    <div className="art-body">
      {nodes.map((node, i) => {
        switch (node.t) {
          case "lead":
            return <p className="art-lead" key={i}>{node.v}</p>;
          case "h":
            return <h3 key={i}>{node.v}</h3>;
          case "quote":
            return <blockquote key={i}>{node.v}</blockquote>;
          case "img":
            return (
              <figure className="art-fig" key={i}>
                <img src={node.src} alt={node.cap || "新闻配图"} loading="lazy" />
                {node.cap && <figcaption>{node.cap}</figcaption>}
              </figure>
            );
          default:
            return <p key={i}>{node.v}</p>;
        }
      })}
    </div>
  );
}

export default function NewsDetail() {
  const { category, slug } = useParams();
  // 以数据库为准：接口确认不存在 → 跳列表；接口不可用 → 才回退本地默认
  const [article, setArticle] = useState(null);
  const [related, setRelated] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fallback, setFallback] = useState(false);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setArticle(null);
    setFallback(false);

    fetchNewsDetail(category, slug).then((res) => {
      if (!alive) return;
      if (res.ok) {
        setArticle(res.article); // 可能为 null：后端确认该文不存在或未发布
      } else {
        setArticle(localDetail(category, slug)); // 接口不可用 → 本地兜底
        setFallback(true);
      }
      setLoading(false);
    });

    return () => { alive = false; };
  }, [category, slug]);

  // 相关阅读独立拉取，不阻塞正文
  useEffect(() => {
    let alive = true;
    fetchNewsList(category).then((res) => {
      if (!alive) return;
      const base = res.ok ? res.items : localList(category);
      setRelated(base.filter((n) => n.slug !== slug).slice(0, 2));
    });
    return () => { alive = false; };
  }, [category, slug]);

  useEffect(() => {
    if (article) document.title = `${article.title} · FLY`;
  }, [article]);

  // 加载中不渲染兜底内容，避免「本地默认」闪现；接口确认不存在再跳列表
  if (loading) return null;
  if (!article) return <Navigate to="/news/company" replace />;

  return (
    <>
      <SiteNav />
      <div className="sub-page news-detail">
        <div className="wrap">
          <nav className="crumb" aria-label="面包屑">
            <Link to="/">首页</Link>
            <span><i className="sep">›</i><Link to="/news/company">新闻</Link></span>
            <span><i className="sep">›</i>
              <Link to={`/news/${article.cat}`}>{CAT_LABEL[article.cat]}</Link></span>
            <span><i className="sep">›</i><em aria-current="page">正文</em></span>
          </nav>

          <article className="art">
            <header className="art-head">
              <div className="cat">{CAT_LABEL[article.cat]}</div>
              <h1>{article.title}</h1>
              <div className="meta-row">
                <span>{formatDate(article.date)}</span>·<span>{article.place || article.editor}</span>
              </div>
            </header>

            <figure className="art-cover">
              <img src={article.cover} alt={article.title} />
            </figure>

            {fallback && (
              <p className="news-note">后端暂不可用，当前展示本地默认内容</p>
            )}

            {article.html ? (
              <>
                {article.lead ? <p className="art-lead">{article.lead}</p> : null}
                <div
                  className="art-body"
                  dangerouslySetInnerHTML={{ __html: article.html }}
                />
              </>
            ) : (
              <Body nodes={article.body || []} />
            )}

            <footer className="art-foot">
              <div className="tags">
                <span># {CAT_LABEL[article.cat]}</span>
                <span># FLY</span>
              </div>
              <Link className="btn ghost back" to={`/news/${article.cat}`}>← 返回{article.cat === "company" ? "企业新闻" : "行业资讯"}列表</Link>
            </footer>
          </article>

          {related.length > 0 && (
            <aside className="related">
              <h2>相关阅读</h2>
              {related.map(n => (
                <Link to={`/news/${n.cat}/${n.slug}`} key={n.slug} className="rel-item">
                  <span className="date">{formatDate(n.date)}</span>
                  <b>{n.title}</b>
                </Link>
              ))}
            </aside>
          )}
        </div>
      </div>
      <SiteFooter />
    </>
  );
}
