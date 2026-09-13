@echo off
setlocal
title TEGAKI H3 + MANGA
set "PORTABLE_ROOT=%~dp0.."
pushd "%PORTABLE_ROOT%"
if errorlevel 1 (
  echo TEGAKI: could not enter the Portable root: "%PORTABLE_ROOT%"
  pause
  exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
  echo TEGAKI: Node.js 18 or newer is required on PATH.
  popd
  pause
  exit /b 1
)

node "%PORTABLE_ROOT%\h3\tools\tegaki_shell_supervisor.mjs" %*
set "TEGAKI_EXIT=%ERRORLEVEL%"
popd
echo TEGAKI shell finished. Review diagnostics above.
pause
exit /b %TEGAKI_EXIT%
