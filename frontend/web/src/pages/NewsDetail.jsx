import { useEffect } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import SiteNav from "../components/SiteNav.jsx";
import SiteFooter from "../components/SiteFooter.jsx";
import { formatDate, getNewsByCat, getNewsDetail } from "../data/siteData.js";

const CAT_LABEL = { company: "企业新闻", industry: "行业资讯" };

// 正文节点渲染：lead/p/h/quote/img
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
  const article = getNewsDetail(category, slug);
  const related = article ? getNewsByCat(article.cat).filter(n => n.slug !== article.slug).slice(0, 2) : [];

  useEffect(() => {
    if (article) document.title = `${article.title} · FLY`;
  }, [article]);

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
                <span>{formatDate(article.date)}</span>·<span>{article.place}</span>·<span>{article.editor}</span>
              </div>
            </header>

            <figure className="art-cover">
              <img src={article.cover} alt={article.title} />
            </figure>

            <Body nodes={article.body} />

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
