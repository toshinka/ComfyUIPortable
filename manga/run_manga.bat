@echo off
setlocal
title TEGAKI MANGA
pushd "%~dp0.."
if errorlevel 1 exit /b 1
where node >nul 2>nul
if errorlevel 1 (
  echo TEGAKI MANGA: Node.js 18 or newer is required on PATH.
  popd
  pause
  exit /b 1
)
node "%~dp0service\run_manga.mjs"
set "MANGA_EXIT=%ERRORLEVEL%"
popd
echo Launcher finished. Review diagnostics above.
pause
exit /b %MANGA_EXIT%
