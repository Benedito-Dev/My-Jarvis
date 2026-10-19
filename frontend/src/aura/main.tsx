import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { DashboardAura } from "./DashboardAura";
import "./aura.css";

document.body.className = "aura-body";

createRoot(document.getElementById("aura-root")!).render(
  <StrictMode>
    <DashboardAura />
  </StrictMode>,
);
