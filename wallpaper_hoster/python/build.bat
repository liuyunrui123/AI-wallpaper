@echo off
echo Python壁纸挂载工具构建脚本
echo ============================

cd /d %~dp0
if exist dist (
    rmdir /s /q dist
)
.venv\Scripts\python.exe -m PyInstaller wallpaper_hoster.py --specpath build
pause
