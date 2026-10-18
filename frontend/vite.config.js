import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import frappeui from 'frappe-ui/vite'

export default defineConfig({
  plugins: [
    frappeui({
      lucideIcons: true,
      frappeProxy: false,
      buildConfig: {
        indexHtmlPath: '../doublet_crm/www/doublet_crm.html',
      },
    }),
    vue(),
  ],

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },

  build: {
    outDir: '../doublet_crm/public/frontend',
    emptyOutDir: true,
  },
})
