import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ConversaJarvis } from "./ConversaJarvis";
import "./conversa.css";

document.body.className = "conversa-body";

createRoot(document.getElementById("conversa-root")!).render(
  <StrictMode>
    <ConversaJarvis />
  </StrictMode>,
);
