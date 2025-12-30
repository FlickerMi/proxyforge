@echo off
REM ProxyForge 启动脚本 (Windows)

echo ===================================
echo   ProxyForge - 代理服务
echo ===================================

REM 检查 Python 版本
python --version

REM 创建虚拟环境(如果不存在)
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 安装依赖...
pip install -r requirements.txt

REM 创建 .env 文件(如果不存在)
if not exist ".env" (
    echo 创建 .env 文件...
    copy .env.example .env
    echo 请根据需要修改 .env 文件中的配置
)

REM 创建日志目录
if not exist "logs" mkdir logs

REM 启动服务
echo 启动 ProxyForge 服务...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
