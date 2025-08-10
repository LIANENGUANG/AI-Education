# 多阶段构建 - 简化版
FROM node:18-alpine as frontend-build

# 设置Alpine国内源
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories

# 设置工作目录
WORKDIR /app/frontend

# 复制前端依赖文件
COPY frontend/package*.json ./

# 设置npm国内源并安装依赖
RUN npm config set registry https://registry.npmmirror.com/ && \
    npm install --omit=dev --no-optional

# 复制前端源代码
COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/tsconfig.json ./

# 构建前端
RUN npm run build

# 后端构建阶段
FROM python:3.10-slim

# 设置环境变量优化pip
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# 设置工作目录
WORKDIR /app

# 安装最小系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# 复制Python依赖文件
COPY backend/requirements.txt ./

# 使用多个pip源提高成功率，简化requirements
RUN pip install --no-cache-dir -i https://pypi.douban.com/simple/ --trusted-host pypi.douban.com -r requirements.txt || \
    pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt || \
    pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./

# 从前端构建阶段复制构建产物到static目录
COPY --from=frontend-build /app/frontend/build ./static

# 创建必要目录
RUN mkdir -p media/documents templates db

# 将React的index.html复制到templates目录供Django使用
RUN cp static/index.html templates/

# 收集静态文件
RUN python manage.py collectstatic --noinput

# 执行数据库迁移
RUN python manage.py migrate

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# 启动命令
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]