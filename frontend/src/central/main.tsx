import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { CentralJarvis } from "./CentralJarvis";
import "./central.css";

document.body.className = "central-body";

createRoot(document.getElementById("central-root")!).render(
  <StrictMode>
    <CentralJarvis />
  </StrictMode>,
);
