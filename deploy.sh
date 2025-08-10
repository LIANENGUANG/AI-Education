#!/bin/bash

echo "🚀 开始部署AI Education系统..."

# 检查Docker是否已安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 检查环境配置文件
if [ ! -f "./backend/.env" ]; then
    echo "⚠️  后端环境配置文件不存在"
    echo "请复制 backend/.env.example 到 backend/.env 并配置相关参数"
    cp backend/.env.example backend/.env
    echo "✅ 已创建 backend/.env 文件，请编辑其中的API密钥等配置"
    echo "   nano backend/.env"
    exit 1
fi

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose down

# 构建并启动服务
echo "🔨 构建镜像..."
docker-compose build

echo "🚀 启动服务..."
docker-compose up -d

# 检查服务状态
echo "📊 检查服务状态..."
sleep 10
docker-compose ps

echo ""
echo "✅ 部署完成！"
echo "🌐 应用访问地址: http://81.70.221.40:9000"
echo "🔧 API地址: http://81.70.221.40:9000/api/"
echo ""
echo "📋 常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  重启服务: docker-compose restart"
echo "  停止服务: docker-compose down"