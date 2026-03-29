@echo off
chcp 65001
echo =====================================
echo       启动前后端一键运行脚本
echo =====================================

echo 启动后端 Python main.py...
start "backend" cmd /k "cd backend && python main.py"

timeout /t 1 /nobreak >nul

echo 启动前端 npm run dev...
start "frontend" cmd /k "cd frontend && npm run serve"

echo 等待前端服务启动...
timeout /t 5 /nobreak >nul

set FRONTEND_URL=http://localhost:8080
echo 正在打开浏览器访问 %FRONTEND_URL%...
start "" "%FRONTEND_URL%"

echo 启动完成！
pause