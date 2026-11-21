import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    // Dentro do Docker o servidor precisa escutar fora do localhost do contêiner.
    host: true,
  },
});
