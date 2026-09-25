import React from "react";
import ReactDOM from "react-dom/client";

import App from "@/App";
import "@/index.css";

// Dark is the default for SecureVault's public pages. Apply the `dark`
// class (Tailwind `darkMode: "class"`) before first render so there is no
// light-theme flash; `useTheme` keeps it in sync afterwards. Runs from the
// bundle (no inline script) so a strict `script-src 'self'` CSP stays happy.
if (typeof window !== "undefined") {
  const stored = window.localStorage.getItem("sv-theme");
  const dark = stored !== "light";
  document.documentElement.classList.toggle("dark", dark);
  document.documentElement.style.colorScheme = dark ? "dark" : "light";
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);