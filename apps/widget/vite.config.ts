import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

import tailwindcss from "@tailwindcss/postcss";
import react from "@vitejs/plugin-react";
import { visualizer } from "rollup-plugin-visualizer";
import type { Plugin } from "vite";
import { defineConfig } from "vitest/config";

import { shadowDomCss } from "./plugins/shadow-dom-css.ts";

const widgetDir = fileURLToPath(new URL(".", import.meta.url));
// Dev ports come from the shell environment (not .env); see .env.example.
const apiPort = process.env.UVICORN_PORT ?? "8000";

function reportGzipSize(): Plugin {
  return {
    name: "cursora:report-gzip-size",
    apply: "build",
    generateBundle(_, bundle) {
      for (const chunk of Object.values(bundle)) {
        if (chunk.type !== "chunk") continue;
        const raw = Buffer.byteLength(chunk.code);
        const gz = gzipSync(chunk.code, { level: 9 }).length;
        const kib = (n: number) => `${(n / 1024).toFixed(1)} KiB`;
        console.log(`\n[cursora] ${chunk.fileName}: ${kib(raw)} raw, ${kib(gz)} gzip`);
      }
    },
  };
}

export default defineConfig(({ command, mode }) => ({
  plugins: [
    react(),
    reportGzipSize(),
    // `pnpm analyze:widget`: per-module treemap with gzip sizes at dist/stats.html.
    mode === "analyze" &&
      visualizer({
        filename: "dist/stats.html",
        template: "treemap",
        gzipSize: true,
        brotliSize: true,
      }),
  ],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  // Tailwind runs through PostCSS (not @tailwindcss/vite) so our shadow-DOM pass runs after it.
  css: { postcss: { plugins: [tailwindcss({ base: widgetDir }), shadowDomCss()] } },
  // Library mode does not replace process.env.NODE_ENV, which React reads.
  define: command === "build" ? { "process.env.NODE_ENV": JSON.stringify("production") } : {},
  server: {
    port: Number(process.env.WIDGET_DEV_PORT ?? 5174),
    strictPort: true,
    proxy: {
      // Same as the admin: /api/* -> FastAPI with the /api prefix stripped. Same origin, so the
      // harness gets the session cookie without CORS.
      "/api": {
        target: `http://127.0.0.1:${apiPort}`,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  build: {
    lib: {
      entry: "src/main.tsx",
      name: "CursoraWidget",
      formats: ["iife"],
      fileName: () => "widget.js",
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    // Process `styles.css?inline` in tests so we can assert what lands in the shadow root.
    css: { include: [/.+/] },
  },
}));
