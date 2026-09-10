import { useEffect, useState } from "react";
import { Card, Row, Col, Statistic, message } from "antd";
import axios from "axios";

// 仪表盘：GET /api/admin/dashboard/stats（需带 Bearer token）
export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const token = localStorage.getItem("fly_admin_token");

  useEffect(() => {
    axios
      .get("/api/admin/dashboard/stats", {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then(({ data }) => setStats(data))
      .catch(() => message.error("加载失败，请确认已登录"));
  }, []);

  const statMap = [
    ["collections", "系列数"], ["items", "款式数"], ["stores", "在线门店"],
    ["news", "在线新闻"], ["published_pages", "已发布页面"], ["contacts_pending", "待处理留言"],
  ];
  return (
    <div>
      <h2>仪表盘</h2>
      <Row gutter={16}>
        {(statMap || []).map(([key, label]) => (
          <Col span={8} key={key} style={{ marginBottom: 16 }}>
            <Card>
              <Statistic title={label} value={stats?.[key] ?? "-"} />
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}
