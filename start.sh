#!/bin/bash
# Python Learning Site 启动脚本

cd /home/admin/.openclaw/workspace/python-learning-site

# 设置 API Key（从环境变量或配置文件读取）
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# 如果 .env 不存在，使用默认配置
export DASHSCOPE_API_KEY="${DASHSCOPE_API_KEY:-sk-你的APIKey}"
export PYTHONUNBUFFERED=1

exec /usr/bin/python app.py
