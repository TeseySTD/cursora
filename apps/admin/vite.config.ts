import { fileURLToPath } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const repoRoot = fileURLToPath(new URL("../..", import.meta.url));
// Dev ports come from the shell environment (not .env); see .env.example.
const apiPort = process.env.UVICORN_PORT ?? "8000";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  // One .env at the repo root for every app (only VITE_* vars reach the browser).
  envDir: repoRoot,
  server: {
    port: Number(process.env.ADMIN_DEV_PORT ?? 5173),
    // Fail instead of silently moving to another port (the widget dev server uses the next one).
    strictPort: true,
    proxy: {
      // Mirrors Nginx in Docker: /api/* -> FastAPI with the /api prefix stripped.
      "/api": {
        target: `http://127.0.0.1:${apiPort}`,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
  },
});
