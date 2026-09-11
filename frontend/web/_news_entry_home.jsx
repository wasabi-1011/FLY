import React from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import Home from "./src/pages/Home.jsx";
createRoot(document.getElementById("root")).render(<MemoryRouter initialEntries={["/"]}><Home /></MemoryRouter>);
