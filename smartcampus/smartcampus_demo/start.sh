#!/bin/bash

echo "====================================="
echo "      启动前后端一键运行脚本"
echo "====================================="

# 启动后端（新开终端窗口，根据你的终端替换）
echo "启动后端 Python main.py ..."
gnome-terminal --tab --title="backend" -- bash -c "cd backend && python3 main.py; exec bash" 2>/dev/null || \
open -a Terminal "backend" && osascript -e 'tell app "Terminal" to do script "cd backend && python3 main.py"' 2>/dev/null

# 等待1秒再开前端
sleep 1

# 启动前端
echo "启动前端 npm run serve"
gnome-terminal --tab --title="frontend" -- bash -c "cd frontend && npm run serve; exec bash" 2>/dev/null || \
open -a Terminal "frontend" && osascript -e 'tell app "Terminal" to do script "cd frontend && npm run dev"' 2>/dev/null

echo "启动完成！"

FRONTEND_URL="http://localhost:8080"
 echo "正在打开浏览器访问 $FRONTEND_URL ..."
 # Linux 打开方式
 xdg-open "$FRONTEND_URL" 2>/dev/null || \

