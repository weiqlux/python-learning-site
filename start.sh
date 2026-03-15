#!/bin/bash
# Python Learning Site 启动脚本

cd /home/admin/.openclaw/workspace/python-learning-site

# 先加载 .env 文件（优先级最高）
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# 如果 .env 没有设置，使用 shell 环境变量或默认值
export DASHSCOPE_API_KEY="${DASHSCOPE_API_KEY:-sk-你的APIKey}"
export PYTHONUNBUFFERED=1

# 打印确认（调试用）
echo "启动服务，API Key: ${DASHSCOPE_API_KEY:0:20}..."

exec /usr/bin/python app.py
