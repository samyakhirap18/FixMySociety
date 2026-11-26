import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  base: process.env.VITE_BASE_PATH || '/',
  plugins: [react()],
  server: { port: 5173 },
  preview: { port: 4173 },
  build: { outDir: 'build' },
  test: {
    environment: 'jsdom',
    setupFiles: './src/setupTests.js',
    css: true,
    restoreMocks: true,
    testTimeout: 20000,
  },
});
