const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '' // 生产环境使用相对路径（Django服务前端和API）
  : 'http://localhost:8000'; // 开发环境使用本地8000端口

export { API_BASE_URL };