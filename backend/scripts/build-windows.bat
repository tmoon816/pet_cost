@echo off
REM 一键打包：在 backend/ 目录下双击或命令行运行
REM 产物路径：backend\dist\pet-cost\pet-cost-server.exe
setlocal

set ROOT=%~dp0..
set BACKEND=%ROOT%\backend
set FRONTEND=%ROOT%\frontend

echo === [1/3] 构建前端 ===
pushd "%FRONTEND%" || goto :err
call npm install || goto :err
call npm run build || goto :err
popd

echo === [2/3] 同步后端依赖 ===
pushd "%BACKEND%" || goto :err
call uv sync --group package || goto :err

echo === [3/3] PyInstaller 打包 ===
if exist build rd /s /q build
if exist dist rd /s /q dist
call uv run pyinstaller pet-cost.spec --noconfirm || goto :err
popd

echo.
echo === 打包完成 ===
echo 产物目录: %BACKEND%\dist\pet-cost
echo 启动入口: pet-cost-server.exe（首次运行会让你设置 admin 密码）
goto :eof

:err
echo.
echo === 打包失败 ===
exit /b 1
