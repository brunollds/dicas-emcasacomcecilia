import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
  root: '.',
  publicDir: 'public',
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        admin: resolve(__dirname, 'admin.html'),
        cozinha: resolve(__dirname, 'cozinha/index.html'),
        tecnologia: resolve(__dirname, 'tecnologia/index.html'),
        casaInteligente: resolve(__dirname, 'casa-inteligente/index.html'),
        salaDeEstar: resolve(__dirname, 'sala-de-estar/index.html'),
        lavanderia: resolve(__dirname, 'lavanderia/index.html'),
        banheiro: resolve(__dirname, 'banheiro/index.html'),
        alimentos: resolve(__dirname, 'alimentos/index.html'),
        outros: resolve(__dirname, 'outros/index.html'),
        damie: resolve(__dirname, 'damie/index.html'),
      },
    },
  },
  server: {
    port: 3000,
    open: true
  },
  appType: 'mpa'
})