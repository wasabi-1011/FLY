import React from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import NewsList from "./src/pages/NewsList.jsx";
createRoot(document.getElementById("root")).render(<MemoryRouter initialEntries={["/news/company"]}><Routes><Route path="/news/:category" element={<NewsList />} /></Routes></MemoryRouter>);
