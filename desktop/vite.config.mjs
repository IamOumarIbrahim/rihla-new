// builds the React screens into dist/ so Electron can open dist/index.html
// "npm run build:demo" makes one self-contained file (dist-demo/index.html) for the online preview
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig(function ({ mode }) {
  const demo = mode === "demo";
  return {
    plugins: demo ? [react(), viteSingleFile()] : [react()],
    // relative paths, because Electron opens the file from disk
    base: "./",
    // the fonts and icons in ../assets are copied next to index.html (not needed in the demo)
    publicDir: demo ? false : "../assets",
    build: {
      outDir: demo ? "dist-demo" : "dist",
      emptyOutDir: true,
      // the demo keeps every picture inside the one file
      assetsInlineLimit: demo ? 100000000 : 4096,
    },
  };
});
