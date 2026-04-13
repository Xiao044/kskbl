#!/bin/bash

# 设置终端标题 (仅部分终端支持)
echo -ne "\033]0;Smart Campus Net Monitor - 系统启动引导\007"

echo "================================================="
echo "    智慧校园网络态势感知系统 - 一键启动脚本"
echo "================================================="

# --- 1. 后端环境与安全依赖检测 ---
echo "[*] 正在检查后端环境 (Python)..."
if [ ! -d "backend/venv" ]; then
    echo "[!] 未检测到虚拟环境，正在初始化并安装核心及安全依赖..."
    cd backend
    # 确保系统中已安装 python3-venv
    python3 -m venv venv || { echo "错误: 请先安装 python3-venv (sudo apt install python3-venv)"; exit 1; }
    source venv/bin/activate
    
    echo "[*] 正在升级 pip 并安装依赖 (包含 JWT 与 原生 bcrypt)..."
    pip install --upgrade pip
    
    # 🌟 核心修改：使用原生 bcrypt 替代 passlib，解决 72 bytes 报错问题
    pip install fastapi uvicorn dpkt openai google-genai "python-jose[cryptography]" bcrypt
    cd ..
    echo "[OK] 后端环境配置完成。"
else
    echo "[OK] 后端虚拟环境已存在。"
    # 增量检查是否有新增依赖（防止手动创建环境漏掉安全库）
    source backend/venv/bin/activate
    pip install "python-jose[cryptography]" bcrypt > /dev/null 2>&1
fi

# --- 2. 前端环境检测 ---
echo "[*] 正在检查前端环境 (Node.js)..."
if [ ! -d "frontend/node_modules" ]; then
    echo "[!] 未检测到前端组件，正在执行 npm install..."
    cd frontend
    npm install || { echo "错误: npm install 失败，请检查 Node 版本"; exit 1; }
    cd ..
    echo "[OK] 前端组件安装完成。"
else
    echo "[OK] 前端组件已就绪。"
fi

echo ""
echo "================================================="
echo "    所有环境已就绪，正在并行启动服务..."
echo "================================================="

# --- 3. 启动后端服务 ---
# 使用 FastAPI 运行 main.py (默认端口 8000)
echo "[*] 启动后端引擎 (FastAPI)..."
if command -v gnome-terminal >/dev/null 2>&1; then
    gnome-terminal --tab --title="NetMonitor-Backend" -- bash -c "cd backend && source venv/bin/activate && python3 main.py; exec bash"
else
    echo "[警告] 未检测到 gnome-terminal，后端将在后台运行，日志：backend.log"
    cd backend && source venv/bin/activate && nohup python3 main.py > ../backend.log 2>&1 &
    cd ..
fi

# 等待 2 秒确保后端端口已监听
sleep 2

# --- 4. 启动前端服务 ---
# 默认使用 Vite/Vue 的开发模式 (根据你的环境，通常是 5173 或 8080)
echo "[*] 启动前端界面 (Vue 3)..."
if command -v gnome-terminal >/dev/null 2>&1; then
    gnome-terminal --tab --title="NetMonitor-Frontend" -- bash -c "cd frontend && npm run serve; exec bash"
else
    echo "[警告] 前端将在后台运行，日志：frontend.log"
    cd frontend && nohup npm run dev > ../frontend.log 2>&1 &
    cd ..
fi

# --- 5. 自动打开浏览器 ---
# 这里默认填写 8080，如果你的 Vue 项目是用 Vite 创建的，请改成 5173
FRONTEND_URL="http://localhost:8080"
echo "[*] 正在尝试打开系统门户: $FRONTEND_URL"
xdg-open "$FRONTEND_URL" 2>/dev/null || echo "[提示] 请手动访问 $FRONTEND_URL"

echo ""
echo "================================================="
echo "    系统启动成功！"
echo "    默认管理账号: admin"
echo "    默认访问密码: admin123"
echo "================================================="
read -p "按回车键保持此窗口运行 (或 Ctrl+C 终止脚本)..."
