@echo off
title Smart Campus Net Monitor - 智能引导脚本
chcp 65001 >nul

echo =====================================
echo    智能环境检测与一键启动 (Windows)
echo =====================================

:: --- 后端环境检测 ---
echo [*] 正在检查后端环境...
if exist "backend\venv" goto BackendReady

echo [!] 未检测到虚拟环境，正在初始化并安装依赖...
cd backend
python -m venv venv
call venv\Scripts\activate
echo [*] 正在安装后端依赖 (fastapi, uvicorn, dpkt, openai)...
pip install fastapi uvicorn dpkt openai google-genai
cd ..
echo [OK] 后端环境配置完成。
goto FrontendCheck

:BackendReady
echo [OK] 后端虚拟环境已存在，跳过安装。

:FrontendCheck
:: --- 前端环境检测 ---
echo [*] 正在检查前端环境...
if exist "frontend\node_modules" goto FrontendReady

echo [!] 未检测到前端组件 (node_modules)，正在安装...
echo [提示] 首次安装可能需要几分钟，请稍候...
cd frontend
call npm install
cd ..
echo [OK] 前端组件安装完成。
goto StartServices

:FrontendReady
echo [OK] 前端组件已存在，跳过安装。

:StartServices
echo.
echo =====================================
echo    所有环境已就绪，正在启动服务...
echo =====================================

:: 1. 启动后端 (新窗口)
start "Net-Monitor-Backend" cmd /k "cd backend && call venv\Scripts\activate && python main.py"

:: 2. 等待 3 秒确保后端初始化
timeout /t 3 /nobreak >nul

:: 3. 启动前端 (新窗口)
start "Net-Monitor-Frontend" cmd /k "cd frontend && npm run serve"

:: 4. 打开浏览器
set FRONTEND_URL=http://localhost:8080
echo [*] 正在打开浏览器访问 %FRONTEND_URL% ...
start %FRONTEND_URL%

echo.
echo [完成] 服务已在独立窗口中运行。
pause