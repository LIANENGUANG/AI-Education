const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'http://81.70.221.40:9000' // 生产环境使用服务器地址和9000端口
  : 'http://localhost:8000'; // 开发环境使用本地8000端口

export { API_BASE_URL };