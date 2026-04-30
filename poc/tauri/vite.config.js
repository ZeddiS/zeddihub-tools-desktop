import { defineConfig } from "vite";

// Tauri serves the frontend; Vite dev server runs at 1420.
export default defineConfig({
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
  },
  envPrefix: ["VITE_", "TAURI_"],
  build: {
    target: "esnext",
    minify: "esbuild",
    sourcemap: false,
  },
});
