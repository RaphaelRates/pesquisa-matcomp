import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  build: {
    outDir: 'dist',
    cssCodeSplit: false,
    rolldownOptions: {
      input: { painel: 'src/main.js' },
      output: {
        entryFileNames: 'painel.js',
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: 'painel[extname]',
      },
    },
  },
});
