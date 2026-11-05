import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// In development, when VITE_API_BASE_URL is not set, the app calls relative
// paths and this proxy forwards them to the local FastAPI server.
// The proxy exists only in `vite dev`; production builds require VITE_API_BASE_URL.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const proxyTarget = env.DEV_API_PROXY_TARGET || "http://127.0.0.1:8000";

  return {
    plugins: [react(), tailwindcss()],
    server: {
      port: 5173,
      proxy: {
        "/api": proxyTarget,
        "/health": proxyTarget,
      },
    },
    build: {
      sourcemap: false,
      chunkSizeWarningLimit: 900,
    },
  };
});
