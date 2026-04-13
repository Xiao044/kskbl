@echo off
chcp 65001 >nul
title 智慧校园网络态势感知系统 - 系统启动引导

echo =================================================
echo     智慧校园网络态势感知系统 - Windows 启动脚本
echo =================================================

:: --- 1. 后端环境与安全依赖检测 ---
echo [*] 正在检查后端环境 (Python)...
if not exist "backend\venv" (
    echo [!] 未检测到虚拟环境，正在初始化并安装核心及安全依赖...
    cd backend
    python -m venv venv
    if errorlevel 1 (
        echo 错误: 请确保已安装 Python 并添加到系统变量 PATH 中。
        pause
        exit /b
    )
    call venv\Scripts\activate
    
    echo [*] 正在升级 pip 并安装依赖...
    python -m pip install --upgrade pip
    
    :: 安装核心依赖
    pip install fastapi uvicorn dpkt openai google-genai "python-jose[cryptography]" bcrypt
    cd ..
    echo [OK] 后端环境配置完成。
) else (
    echo [OK] 后端虚拟环境已存在。
    call backend\venv\Scripts\activate
    :: 增量检查安全库
    pip install "python-jose[cryptography]" bcrypt >nul 2>&1
)

:: --- 2. 前端环境检测 ---
echo [*] 正在检查前端环境 (Node.js)...
if not exist "frontend\node_modules" (
    echo [!] 未检测到前端组件，正在执行 npm install...
    cd frontend
    call npm install
    if errorlevel 1 (
        echo 错误: npm install 失败，请检查 Node.js 是否安装。
        pause
        exit /b
    )
    cd ..
    echo [OK] 前端组件安装完成。
) else (
    echo [OK] 前端组件已就绪。
)

echo.
echo =================================================
echo     所有环境已就绪，正在并行启动服务...
echo =================================================

:: --- 3. 启动后端服务 ---
echo [*] 启动后端引擎 (FastAPI)...
:: 使用 start 命令新开一个窗口运行后端
start "NetMonitor-Backend" cmd /k "cd backend && call venv\Scripts\activate && python main.py"

:: 等待 3 秒确保后端端口已监听
timeout /t 3 /nobreak >nul

:: --- 4. 启动前端服务 ---
echo [*] 启动前端界面 (Vue 3)...
:: 🌟 核心修复：添加 --host 0.0.0.0 确保局域网可访问
start "NetMonitor-Frontend" cmd /k "cd frontend && npm run serve -- --host 0.0.0.0"

:: --- 5. 自动打开浏览器 ---
:: 默认 Vue 端口通常为 8080
set FRONTEND_URL=http://localhost:8080
echo [*] 正在尝试打开系统门户: %FRONTEND_URL%
timeout /t 5 /nobreak >nul
start %FRONTEND_URL%

echo.
echo =================================================
echo     系统启动成功！
echo     默认管理账号: admin
echo     默认访问密码: admin123
echo.
echo     提示：如果局域网同学无法访问，请检查 Windows 防火墙
echo     是否允许了 8000 和 8080 端口。
echo =================================================
pause