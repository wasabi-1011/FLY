import { useState } from "react";
import { Form, Input, Button, Card, message } from "antd";
import axios from "axios";

// 后台登录：POST /api/admin/auth/login (OAuth2 Password 表单)，存 token 到 localStorage
export default function Login() {
  const [loading, setLoading] = useState(false);

  async function onFinish(values) {
    setLoading(true);
    try {
      const fd = new URLSearchParams();
      fd.append("username", values.username);
      fd.append("password", values.password);
      const { data } = await axios.post("/api/admin/auth/login", fd, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      localStorage.setItem("fly_admin_token", data.access_token);
      localStorage.setItem("fly_admin_role", data.role);
      message.success("登录成功");
      window.location.href = "/dashboard";
    } catch (e) {
      message.error("登录失败：" + (e.response?.data?.detail || "请重试"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 380, margin: "80px auto" }}>
      <Card title="FLY 后台管理">
        <Form onFinish={onFinish} layout="vertical">
          <Form.Item name="username" label="账号" rules={[{ required: true }]}>
            <Input autoComplete="username" />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true }]}>
            <Input.Password autoComplete="current-password" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block loading={loading}>
            登录
          </Button>
        </Form>
      </Card>
    </div>
  );
}
