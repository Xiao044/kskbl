#!/bin/bash

# 设置终端标题 (仅部分终端支持)
echo -ne "\033]0;Smart Campus Net Monitor - 智能引导脚本\007"

echo "====================================="
echo "    智能环境检测与一键启动 (Linux)"
echo "====================================="

# --- 后端环境检测 ---
echo "[*] 正在检查后端环境..."
if [ ! -d "backend/venv" ]; then
    echo "[!] 未检测到虚拟环境，正在初始化并安装依赖..."
    cd backend
    # 确保系统中已安装 python3-venv
    python3 -m venv venv || { echo "错误: 请先安装 python3-venv (sudo apt install python3-venv)"; exit 1; }
    source venv/bin/activate
    echo "[*] 正在安装后端依赖 (fastapi, uvicorn, dpkt, openai, google-genai)..."
    pip install --upgrade pip
    pip install fastapi uvicorn dpkt openai google-genai
    cd ..
    echo "[OK] 后端环境配置完成。"
else
    echo "[OK] 后端虚拟环境已存在，跳过安装。"
fi

# --- 前端环境检测 ---
echo "[*] 正在检查前端环境..."
if [ ! -d "frontend/node_modules" ]; then
    echo "[!] 未检测到前端组件 (node_modules)，正在安装..."
    echo "[提示] 首次安装可能需要几分钟，请确保已安装 Node.js 和 npm..."
    cd frontend
    npm install || { echo "错误: npm install 失败，请检查网络和 Node 版本"; exit 1; }
    cd ..
    echo "[OK] 前端组件安装完成。"
else
    echo "[OK] 前端组件已存在，跳过安装。"
fi

echo ""
echo "====================================="
echo "    所有环境已就绪，正在启动服务..."
echo "====================================="

# 1. 启动后端 (使用 gnome-terminal 新标签页，如果不可用则在后台运行)
echo "[*] 启动后端服务..."
if command -v gnome-terminal >/dev/null 2>&1; then
    gnome-terminal --tab --title="Backend" -- bash -c "cd backend && source venv/bin/activate && python3 main.py; exec bash"
else
    echo "[警告] 未检测到 gnome-terminal，后端将在后台运行，日志输出至 backend.log"
    cd backend && source venv/bin/activate && nohup python3 main.py > ../backend.log 2>&1 &
    cd ..
fi

# 2. 等待 3 秒确保后端初始化
sleep 3

# 3. 启动前端
echo "[*] 启动前端服务..."
if command -v gnome-terminal >/dev/null 2>&1; then
    gnome-terminal --tab --title="Frontend" -- bash -c "cd frontend && npm run serve; exec bash"
else
    echo "[警告] 未检测到 gnome-terminal，前端将在后台运行，日志输出至 frontend.log"
    cd frontend && nohup npm run serve > ../frontend.log 2>&1 &
    cd ..
fi

# 4. 自动打开浏览器 (xdg-open 是 Linux 通用命令)
FRONTEND_URL="http://localhost:8080"
echo "[*] 正在尝试打开浏览器访问 $FRONTEND_URL ..."
xdg-open "$FRONTEND_URL" 2>/dev/null || echo "[提示] 请手动访问 $FRONTEND_URL"

echo ""
echo "[完成] 服务启动流程已结束。"
echo "[提示] 如果窗口闪退，请在当前终端手动运行: ./start.sh 观察报错信息。"
read -p "按回车键退出本窗口..."
