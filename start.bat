@echo off
chcp 936 >nul
cd /d "%~dp0"
title FLY Launcher
setlocal

rem 选择可用的 Python 解释器：优先项目 .venv，其次 Python311，最后 PATH 里的 python
set "PY=%~dp0backend\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=C:\Program Files\Python311\python.exe"
if not exist "%PY%" set "PY=python"

:menu
cls
echo ============================================
echo    FLY 品牌官网  一键启动
echo ============================================
echo.
echo   1  Start ALL       全部启动（前台官网 3000 + 后台管理 8000）
echo   2  Backend only    仅启动后台管理（8000）
echo   3  Frontend only   仅启动前台官网（3000）
echo   4  Stop all        停止全部服务
echo   5  Reset database  恢复初始数据（重置为种子状态）
echo   6  DB status       查看数据库状态
echo   0  Quit            退出
echo.
set "choice="
set /p choice=Select [0-6]: 
if "%choice%"=="1" goto ALL
if "%choice%"=="2" goto BACKEND
if "%choice%"=="3" goto FRONT
if "%choice%"=="4" goto STOP
if "%choice%"=="5" goto RESET
if "%choice%"=="6" goto DBSTATUS
if "%choice%"=="0" goto END
goto menu

:ALL
call :CHECK 8000
call :CHECK 3000
echo [1/2] 启动后端 API 与后台管理 ...
start "FLY-Backend-8000" /D "%~dp0backend" cmd.exe /k ""%PY%" -m uvicorn app.main:app --port 8000"
echo [2/2] 启动前台官网 ...
start "FLY-Frontend-3000" /D "%~dp0frontend\web" cmd.exe /k "npm run dev"
goto OPEN

:BACKEND
call :CHECK 8000
echo 启动后端 API 与后台管理 ...
start "FLY-Backend-8000" /D "%~dp0backend" cmd.exe /k ""%PY%" -m uvicorn app.main:app --port 8000"
timeout /t 6 >nul
start "" http://localhost:8000/admin/index.html
echo.
echo 后台管理已打开：http://localhost:8000/admin/index.html
echo 关闭新开的窗口即可停止后端服务。
goto HOLD

:FRONT
call :CHECK 3000
echo 启动前台官网 ...
start "FLY-Frontend-3000" /D "%~dp0frontend\web" cmd.exe /k "npm run dev"
timeout /t 7 >nul
start "" http://localhost:3000
echo.
echo 前台官网已打开：http://localhost:3000
echo 关闭新开的窗口即可停止前台服务。
goto HOLD

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
echo 新开的两个窗口分别是后端与前台服务，关闭窗口即停止对应服务。
goto HOLD

:STOP
echo 正在停止 8000 与 3000 端口上的服务 ...
call :KILLPORT 8000
call :KILLPORT 3000
call :KILLUVICORN
echo 已停止。
goto HOLD

:RESET
echo.
echo 恢复初始数据会先用初始快照覆盖数据库，当前库里的改动都会丢失。
set "confirm="
set /p confirm=Confirm reset? [y/N]: 
if /i not "%confirm%"=="y" goto menu
call :KILLPORT 8000
call :KILLUVICORN
echo.
"%PY%" "%~dp0backend\重置数据库.py"
echo.
echo 数据已恢复为初始状态，可以回菜单选择 1 启动。
goto HOLD

:DBSTATUS
echo.
"%PY%" "%~dp0backend\重置数据库.py" --show
goto HOLD

:CHECK
netstat -ano | findstr LISTENING | findstr :%~1 >nul
if %errorlevel%==0 echo [提示] 端口 %~1 已被占用，如启动失败请先选 4 停止服务。
exit /b

:KILLPORT
for /f "tokens=5" %%p in ('netstat -ano ^| findstr LISTENING ^| findstr :%~1') do taskkill /F /PID %%p >nul 2>&1
exit /b

:KILLUVICORN
for /f "skip=1 tokens=*" %%p in ('wmic process where "name='python.exe' and commandline like '%%uvicorn%%'" get processid 2^>nul') do taskkill /F /PID %%p >nul 2>&1
exit /b

:HOLD
echo.
pause
goto menu

:END
endlocal
exit /b
