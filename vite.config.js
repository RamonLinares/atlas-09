import { defineConfig } from 'vite';
import { resolve } from 'node:path';

// Two pages share one bundle graph: the asset lab and the combat arena.
export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        lab: resolve(__dirname, 'index.html'),
        combat: resolve(__dirname, 'combat.html'),
      },
    },
  },
});
