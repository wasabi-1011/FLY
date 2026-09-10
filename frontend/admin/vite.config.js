import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 后台 Admin（React SPA + Ant Design）
// 开发代理：/api 转发到本地 FastAPI 后端
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
  },
});
