@echo off
cd /d %~dp0
cd WallpaperHosterLively
dotnet publish -c Release -r win-x64 -o out
pause