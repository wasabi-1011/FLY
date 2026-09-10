import { useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import Home from "./pages/Home.jsx";
import Products from "./pages/Products.jsx";
import CategoryPage from "./pages/CategoryPage.jsx";
import HotPage from "./pages/HotPage.jsx";
import ItemDetail from "./pages/ItemDetail.jsx";
import NewsList from "./pages/NewsList.jsx";
import NewsDetail from "./pages/NewsDetail.jsx";
import Stores from "./pages/Stores.jsx";
import AboutStory from "./pages/AboutStory.jsx";
import AboutBrand from "./pages/AboutBrand.jsx";
import AboutHistory from "./pages/AboutHistory.jsx";
import Contact from "./pages/Contact.jsx";

// 切页回到顶部（SPA 阶段体验；SSR 二期可去掉）
function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <Routes>
        <Route path="/" element={<Home />} />
        {/* 产品中心（聚合）/ 热门 / 品类 */}
        <Route path="/products" element={<Products />} />
        <Route path="/products/hot" element={<HotPage />} />
        <Route path="/products/:category" element={<CategoryPage />} />
        {/* 单品详情（左图右文）：/products/:category/:code */}
        <Route path="/products/:category/:code" element={<ItemDetail />} />
        {/* 新闻列表 / 详情（/news/:category 必须用动态参数，NewsList 用 useParams 拿 category）*/}
        <Route path="/news/:category" element={<NewsList />} />
        <Route path="/news/:category/:slug" element={<NewsDetail />} />
        {/* 门店 */}
        <Route path="/stores" element={<Stores />} />
        {/* 关于我们 / 联系我们（固定页） */}
        <Route path="/about" element={<AboutStory />} />
        <Route path="/about/brand" element={<AboutBrand />} />
        <Route path="/about/history" element={<AboutHistory />} />
        <Route path="/contact" element={<Contact />} />
        {/* 未知路由回首页 */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
