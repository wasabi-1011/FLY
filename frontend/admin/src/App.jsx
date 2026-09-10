import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Layout, Menu } from "antd";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";

// 后台 Admin SPA 骨架
export default function App() {
  const token = localStorage.getItem("fly_admin_token");
  const items = [
    { key: "/dashboard", label: "仪表盘" },
    { key: "/content", label: "内容管理" },
    { key: "/catalog", label: "商品门店" },
    { key: "/contacts", label: "留言管理" },
  ];
  return (
    <BrowserRouter>
      {!token ? (
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      ) : (
        <Layout style={{ minHeight: "100vh" }}>
          <Layout.Sider>
            <Menu theme="dark" mode="inline" items={items} />
          </Layout.Sider>
          <Layout.Content style={{ padding: 24 }}>
            <Routes>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Layout.Content>
        </Layout>
      )}
    </BrowserRouter>
  );
}
