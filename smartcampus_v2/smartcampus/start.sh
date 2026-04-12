#!/bin/bash

echo "====================================="
echo "      启动前后端一键运行脚本 (Linux版)"
echo "====================================="

# 1. 启动后端（新开终端窗口，进入backend目录，激活虚拟环境并启动）
echo "启动后端 Python main.py (使用虚拟环境) ..."
gnome-terminal --tab --title="backend" -- bash -c "cd backend && source venv/bin/activate && python3 main.py; exec bash" 2>/dev/null

# 等待2秒确保后端启动完毕
sleep 2

# 2. 启动前端（新开终端窗口）
echo "启动前端 npm run serve ..."
gnome-terminal --tab --title="frontend" -- bash -c "cd frontend && npm run serve; exec bash" 2>/dev/null

echo "后台进程启动完成！"

# 3. 自动打开浏览器
FRONTEND_URL="http://localhost:8080"
echo "正在打开浏览器访问 $FRONTEND_URL ..."
xdg-open "$FRONTEND_URL" 2>/dev/null
