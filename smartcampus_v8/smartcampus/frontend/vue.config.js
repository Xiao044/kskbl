const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  lintOnSave: false, // 保持你原有的设置
  // 👇 加上这块 devServer 配置，强行把“门”打开
  devServer: {
    host: '0.0.0.0', // 0.0.0.0 表示允许局域网内所有 IP 访问
    port: 8080       // 固定你的端口为 8080，方便别人记
  }
})