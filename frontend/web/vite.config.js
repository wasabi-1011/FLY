import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 前台 Web（React SSR 预留）
// 开发代理：/api 转发到本地 FastAPI 后端（见 backend，默认 8000）
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      // 后台上传的图片（/uploads/xxx.jpg）同样转发到后端
      "/uploads": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
  },
});
