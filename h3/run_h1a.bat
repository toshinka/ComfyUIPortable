@echo off
setlocal
set "PORTABLE_ROOT=%~dp0.."
pushd "%PORTABLE_ROOT%"

if not exist "%PORTABLE_ROOT%\output\h3\video" mkdir "%PORTABLE_ROOT%\output\h3\video"
if not exist "%PORTABLE_ROOT%\output\h3\tests" mkdir "%PORTABLE_ROOT%\output\h3\tests"
if not exist "%PORTABLE_ROOT%\output\h3\h1a_native_user" mkdir "%PORTABLE_ROOT%\output\h3\h1a_native_user"
if not exist "%PORTABLE_ROOT%\output\h3\h1a_native_temp" mkdir "%PORTABLE_ROOT%\output\h3\h1a_native_temp"

start "TEGAKI H3 Native Backend" /b "%PORTABLE_ROOT%\python_embeded\python.exe" "%PORTABLE_ROOT%\ComfyUI\main.py" ^
  --listen 127.0.0.1 --port 8188 ^
  --disable-auto-launch --disable-manager --disable-all-custom-nodes ^
  --extra-model-paths-config "%PORTABLE_ROOT%\h3\config\extra_model_paths.yaml" ^
  --output-directory "%PORTABLE_ROOT%\output\h3" ^
  --input-directory "%PORTABLE_ROOT%\output\h3\tests" ^
  --user-directory "%PORTABLE_ROOT%\output\h3\h1a_native_user" ^
  --temp-directory "%PORTABLE_ROOT%\output\h3\h1a_native_temp" ^
  --database-url sqlite:///:memory: --log-stdout

start "TEGAKI H3 Minimum Video Skin" /b "%PORTABLE_ROOT%\python_embeded\python.exe" "%PORTABLE_ROOT%\h3\app\server.py" ^
  --host 127.0.0.1 --port 8190 --comfy-url http://127.0.0.1:8188 --output-dir output/h3

if /I not "%TEGAKI_H3_NO_BROWSER%"=="1" (
  timeout /t 4 /nobreak >nul
  start "" http://127.0.0.1:8190/
)

popd
endlocal
