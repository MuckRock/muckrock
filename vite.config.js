import { defineConfig } from "vite";
import inject from "@rollup/plugin-inject";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
  base: process.env.VITE_ASSET_BASE || "/static/",
  plugins: [
    inject({
      include: ["**/*.js", "**/*.jsx"],
      $: "jquery",
      jQuery: "jquery",
    }),
  ],
  build: {
    manifest: "manifest.json",
    outDir: path.resolve(__dirname, "muckrock/assets/dist"),
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, "muckrock/assets/entry.js"),
        foiamachine: path.resolve(__dirname, "muckrock/foiamachine/assets/entry.js"),
        docViewer: path.resolve(__dirname, "muckrock/assets/js/docViewer.js"),
      },
    },
  },
  esbuild: {
    loader: "jsx",
    include: /\.(jsx?|tsx?)$/,
    jsxFactory: "React.createElement",
    jsxFragment: "React.Fragment",
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "muckrock/assets"),
    },
    extensions: [".js", ".jsx", ".json"],
  },
  server: {
    port: 4200,
    host: true,
    cors: true,
    watch: {
      usePolling: true, // Important for Docker
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        // Add any SCSS options here if needed
      },
    },
  },
});
