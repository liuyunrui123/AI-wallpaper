@echo off
REM 一键打包 Flask 后端为 app.exe，产物输出到 backend/app.exe
cd /d %~dp0

REM 用.venv虚拟环境的 python 调用 pyinstaller，确保依赖无遗漏
.venv\Scripts\python.exe -m PyInstaller --onefile app.py --distpath . --workpath build --specpath build --hidden-import=engineio.async_drivers.threading --hidden-import=gevent --hidden-import=engineio.async_drivers.gevent
if exist app.exe (
    echo 打包成功，已生成 app.exe
) else (
    echo 打包失败，请检查错误信息
)
pause
