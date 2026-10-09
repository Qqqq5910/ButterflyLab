import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    proxy: {
      '/api': { target: process.env.BUTTERFLYLAB_DEV_BACKEND || 'http://127.0.0.1:8001', changeOrigin: true },
    },
  },
});
