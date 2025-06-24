const { defineConfig } = require('@vue/cli-service');

const API_PORT = process.env.FLASK_API_PORT || '9000';

module.exports = defineConfig({
  publicPath: './', // 关键：让静态资源路径变为相对路径，兼容 Electron file://
  configureWebpack: {
    entry: './src/main.ts',
  },
  devServer: {
    proxy: {
      '/api': {
        target: `http://localhost:${API_PORT}`,
        changeOrigin: true,
        pathRewrite: { '^/api': '/api' }
      },
      '/static': {
        target: `http://localhost:${API_PORT}`,
        changeOrigin: true,
        pathRewrite: { '^/static': '/static' }
      }
    }
  }
});
