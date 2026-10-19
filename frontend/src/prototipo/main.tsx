import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { DashboardPrototipo } from "./DashboardPrototipo";
import "./dashboard.css";

document.body.className = "prototipo-body";

createRoot(document.getElementById("prototipo-root") as HTMLElement).render(
  <StrictMode>
    <DashboardPrototipo />
  </StrictMode>,
);
