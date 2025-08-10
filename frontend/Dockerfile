# 多阶段构建：第一阶段 - 构建阶段
FROM node:18-alpine as build

# 设置工作目录
WORKDIR /app

# 复制 package 文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 第二阶段 - 生产阶段
FROM nginx:alpine

# 删除默认的 nginx 静态资源
RUN rm -rf /usr/share/nginx/html/*

# 从构建阶段复制构建结果
COPY --from=build /app/build /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]