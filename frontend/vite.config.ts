import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    open: false,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/feeds": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/headways": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/coverage": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/export": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/ingest": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
