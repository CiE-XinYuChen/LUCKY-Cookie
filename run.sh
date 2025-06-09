#!/bin/bash

# 宿舍抽签系统启动脚本

echo "=== 宿舍抽签系统启动 ==="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python 3.7+"
    exit 1
fi

# 检查PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "警告: 未找到 PostgreSQL，请确保已安装并配置好数据库"
fi

# 检查Redis
if ! command -v redis-cli &> /dev/null; then
    echo "警告: 未找到 Redis，请确保已安装并启动 Redis 服务"
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装依赖包..."
pip install -r requirements.txt

# 检查环境配置文件
if [ ! -f ".env" ]; then
    echo "创建环境配置文件..."
    cp .env.example .env
    echo "请编辑 .env 文件配置数据库和Redis连接信息"
fi

# 创建uploads目录
mkdir -p uploads

# 设置环境变量
export FLASK_ENV=development
export FLASK_DEBUG=True

echo "=== 启动应用 ==="
echo "访问地址: http://localhost:32228"
echo "默认管理员账户: admin / admin123"
echo "按 Ctrl+C 停止服务"
echo ""

# 启动应用
python3 app.py