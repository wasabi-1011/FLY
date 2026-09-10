import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import SiteNav from "../components/SiteNav.jsx";
import SiteFooter from "../components/SiteFooter.jsx";
import PageHero from "../components/PageHero.jsx";
import AboutTabs from "../components/AboutTabs.jsx";
import { CONTACT, CONTACT_TOPICS } from "../data/aboutData.js";

// /contact 联系我们：联系信息 + 留言/合作垂询表单
// 表单当前为纯前端演示（校验 + 成功态）；二期提交到后台「留言管理」接口，与后台 CONTENT_OPS 留言模块闭环。
export default function Contact() {
  const [form, setForm] = useState({ name: "", contact: "", topic: "business", content: "" });
  const [err, setErr] = useState({});
  const [sent, setSent] = useState(null);

  useEffect(() => { document.title = "联系我们 · FLY"; }, []);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = (e) => {
    e.preventDefault();
    const next = {};
    if (!form.name.trim()) next.name = "请填写称呼";
    if (!form.contact.trim()) next.contact = "请填写电话或邮箱";
    else if (!/^[\w.+-]+@[\w-]+(\.[\w-]+)+$/.test(form.contact.trim()) && !/^1\d{10}$/.test(form.contact.trim()))
      next.contact = "请填写有效的手机号或邮箱";
    if (!form.content.trim()) next.content = "请填写留言内容";
    else if (form.content.trim().length < 10) next.content = "内容至少 10 个字";
    setErr(next);
    if (Object.keys(next).length) return;
    const no = `MS${Date.now().toString().slice(-8)}`;
    setSent({ no, topic: CONTACT_TOPICS.find((t) => t.v === form.topic)?.l });
  };

  const again = () => { setSent(null); setForm({ name: "", contact: "", topic: "business", content: "" }); setErr({}); };

  return (
    <>
      <SiteNav />
      <div className="sub-page">
        <PageHero
          crumbs={[{ label: "关于我们", to: "/about" }, { label: "联系我们" }]}
          title="联系我们"
          en="CONTACT"
          sub={CONTACT.lead}
          bg="/pic/storefront-02.jpg"
        />
        <div className="wrap">
          <AboutTabs />

          {/* 联系信息 */}
          <section className="contact-cards" aria-label="联系方式">
            {CONTACT.items.map((c) => (
              <div className="c-card" key={c.k}>
                <h3>{c.k}</h3>
                <p>{c.v}</p>
              </div>
            ))}
          </section>
          <p className="contact-note">{CONTACT.note} 门店地图见
            <Link className="more" to="/stores" style={{ marginLeft: 4 }}>门店查询 →</Link>
          </p>

          {/* 留言 / 合作垂询表单 */}
          <section className="contact-form" aria-label="留言与合作垂询">
            <div className="sec-head" style={{ marginBottom: 22 }}>
              <div className="eyebrow" style={{ marginBottom: 10 }}>留言 / 垂询</div>
              <h2 className="sec-title">给我们留言</h2>
            </div>

            {sent ? (
              <div className="form-sent" role="status">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 6 9 17l-5-5" /></svg>
                <h3>留言已收到</h3>
                <p>编号 <b>{sent.no}</b> · 类型「{sent.topic}」</p>
                <p className="dim">我们会尽快通过你留下的联系方式回复（当前为演示环境，留言仅在本页展示，二期将提交至后台「留言管理」）。</p>
                <button className="btn" onClick={again}>再写一条</button>
              </div>
            ) : (
              <form className="c-form" onSubmit={submit} noValidate>
                <div className="f-row">
                  <label className="f-field">
                    <span>称呼 <i>*</i></span>
                    <input type="text" value={form.name} onChange={set("name")} placeholder="怎么称呼你" maxLength={20} />
                    {err.name && <em className="f-err">{err.name}</em>}
                  </label>
                  <label className="f-field">
                    <span>联系方式 <i>*</i></span>
                    <input type="text" value={form.contact} onChange={set("contact")} placeholder="手机号或邮箱" maxLength={40} />
                    {err.contact && <em className="f-err">{err.contact}</em>}
                  </label>
                </div>
                <label className="f-field">
                  <span>留言类型</span>
                  <select value={form.topic} onChange={set("topic")}>
                    {CONTACT_TOPICS.map((t) => <option value={t.v} key={t.v}>{t.l}</option>)}
                  </select>
                </label>
                <label className="f-field">
                  <span>留言内容 <i>*</i></span>
                  <textarea rows={5} value={form.content} onChange={set("content")} placeholder="请简单描述你的需求（至少 10 个字）" maxLength={500} />
                  {err.content && <em className="f-err">{err.content}</em>}
                </label>
                <div className="f-actions">
                  <button type="submit" className="btn">提交留言</button>
                  <span className="f-hint">演示环境 · 二期对接后台留言管理接口</span>
                </div>
              </form>
            )}
          </section>
        </div>
      </div>
      <SiteFooter />
    </>
  );
}
