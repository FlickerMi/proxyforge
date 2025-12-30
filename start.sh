#!/bin/bash

# ProxyForge 启动脚本

echo "==================================="
echo "  ProxyForge - 代理服务"
echo "==================================="

# 检查 Python 版本
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python 版本: $python_version"

# 创建虚拟环境(如果不存在)
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 创建 .env 文件(如果不存在)
if [ ! -f ".env" ]; then
    echo "创建 .env 文件..."
    cp .env.example .env
    echo "请根据需要修改 .env 文件中的配置"
fi

# 创建日志目录
mkdir -p logs

# 启动服务
echo "启动 ProxyForge 服务..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
