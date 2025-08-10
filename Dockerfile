# 多阶段构建
FROM node:18-alpine as frontend-build

# 设置工作目录
WORKDIR /app/frontend

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装前端依赖
RUN npm ci --only=production

# 复制前端源代码
COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/tsconfig.json ./

# 构建前端
RUN npm run build

# 后端构建阶段
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libmagic1 \
    libmagic-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 复制并安装Python依赖
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./

# 从前端构建阶段复制构建产物
COPY --from=frontend-build /app/frontend/build ./static

# 重新组织静态文件结构
RUN cd static && \
    if [ -d "static" ]; then \
        mv static/* . && \
        rmdir static; \
    fi

# 创建必要目录
RUN mkdir -p media/documents staticfiles

# 收集静态文件
RUN python manage.py collectstatic --noinput

# 执行数据库迁移
RUN python manage.py migrate

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# 启动命令
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]