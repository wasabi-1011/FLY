@echo off
cd /d "%~dp0"
title FLY Launcher

echo ============================================
echo    FLY 品牌官网 - 一键启动
echo ============================================
echo.
echo   1 - 全部启动（前台官网 + 后台管理）
echo   2 - 仅启动后台管理（端口 8000）
echo   3 - 仅启动前台官网（端口 3000）
echo   4 - 停止所有服务
echo.
set /p choice=请输入序号 [1/2/3/4] 后回车:

if "%choice%"=="1" goto ALL
if "%choice%"=="2" goto BACKEND
if "%choice%"=="3" goto FRONT
if "%choice%"=="4" goto STOP
goto ALL

:ALL
call :CHECK8000
call :CHECK3000
echo [1/2] 启动后端 API + 后台管理 ...
start "FLY-Backend :8000" /D "%~dp0backend" cmd.exe /k ".venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"
echo [2/2] 启动前台官网 ...
start "FLY-Frontend :3000" /D "%~dp0frontend\web" cmd.exe /k npm run dev
goto OPEN

:BACKEND
call :CHECK8000
echo 启动后端 API + 后台管理 ...
start "FLY-Backend :8000" /D "%~dp0backend" cmd.exe /k ".venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"
goto OPENADMIN

:FRONT
call :CHECK3000
echo 启动前台官网 ...
start "FLY-Frontend :3000" /D "%~dp0frontend\web" cmd.exe /k npm run dev
goto OPENWEB

:OPEN
echo.
echo 等待服务就绪 ...
timeout /t 8 >nul
start "" http://localhost:3000
start "" http://localhost:8000/admin/index.html
echo.
echo 已打开两个页面：
echo   前台官网   http://localhost:3000
echo   后台管理   http://localhost:8000/admin/index.html
echo.
echo 新开的窗口分别是后端与前台服务，关掉窗口即停止对应服务。
goto END

:OPENADMIN
timeout /t 6 >nul
start "" http://localhost:8000/admin/index.html
echo 后台管理已打开：http://localhost:8000/admin/index.html
goto END

:OPENWEB
timeout /t 7 >nul
start "" http://localhost:3000
echo 前台官网已打开：http://localhost:3000
goto END

:STOP
echo 正在停止端口 8000 / 3000 上的服务 ...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr LISTENING ^| findstr :8000') do taskkill /F /PID %%p >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr LISTENING ^| findstr :3000') do taskkill /F /PID %%p >nul 2>&1
echo 已停止。
goto END

:CHECK8000
netstat -ano | findstr LISTENING | findstr :8000 >nul
if %errorlevel%==0 echo [提示] 端口 8000 已被占用，若启动失败请先选 4 停止服务。
exit /b

:CHECK3000
netstat -ano | findstr LISTENING | findstr :3000 >nul
if %errorlevel%==0 echo [提示] 端口 3000 已被占用，若启动失败请先选 4 停止服务。
exit /b

:END
echo.
pause
