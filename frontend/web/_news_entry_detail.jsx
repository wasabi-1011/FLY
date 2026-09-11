import React from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import NewsDetail from "./src/pages/NewsDetail.jsx";
createRoot(document.getElementById("root")).render(<MemoryRouter initialEntries={["/news/company/aw-2026-global-launch"]}><Routes><Route path="/news/:category/:slug" element={<NewsDetail />} /></Routes></MemoryRouter>);
