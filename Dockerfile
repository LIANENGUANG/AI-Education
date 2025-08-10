# 多阶段构建
# 第一阶段：构建前端
FROM node:18-alpine as frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

# 第二阶段：构建后端
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libmagic1 \
    libmagic-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制后端依赖文件并安装
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./

# 从前端构建阶段复制静态文件
COPY --from=frontend-build /app/frontend/build ./static/

# 创建媒体文件目录
RUN mkdir -p /app/media/documents

# 收集静态文件
RUN python manage.py collectstatic --noinput

# 运行数据库迁移
RUN python manage.py migrate

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]