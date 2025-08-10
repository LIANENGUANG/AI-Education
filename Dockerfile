# 后端构建阶段 - 简化版
FROM python:3.10-slim

# 设置环境变量优化pip
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# 设置工作目录为项目根目录
WORKDIR /app

# 安装最小系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# 复制Python依赖文件
COPY backend/requirements.txt ./backend/

# 使用官方PyPI源安装Python依赖
RUN pip install --no-cache-dir -r backend/requirements.txt

# 复制整个项目结构
COPY backend/ ./backend/
COPY frontend/build/ ./frontend/build/

# 切换到backend目录执行Django命令
WORKDIR /app/backend

# 执行数据库迁移
RUN python manage.py migrate

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# 启动命令
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]