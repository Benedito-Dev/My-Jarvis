import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { PresencaJarvis } from "./PresencaJarvis";
import "./presenca.css";

document.body.className = "presenca-body";

createRoot(document.getElementById("presenca-root")!).render(
  <StrictMode>
    <PresencaJarvis />
  </StrictMode>,
);
