@echo off
setlocal
title TEGAKI
rem TEGAKI daily entrypoint (Card TEGAKI-MULTI-ENGINE-LAUNCHER-AND-AVAILABILITY-SYNC-1).
rem Starts or reuses, in order: EasyReforge Integration Runtime (7862), H3 Native (8188),
rem H3 shell (8190), Manga backend (8189) and Manga workspace (8191), then opens the TEGAKI shell.
rem Verified pre-existing services are reused and left running at shutdown; unknown listeners on a
rem required port fail closed and are never killed.  The ReForge browser tab is not auto-opened.
rem Lower-level/debug launchers remain: h3\run_h3.bat, manga\run_manga.bat, and the Integration
rem runtime's own Reforge.bat (normal ReForge GUI).
set "PORTABLE_ROOT=%~dp0"
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

node "%PORTABLE_ROOT%h3\tools\tegaki_shell_supervisor.mjs" --with-easyreforge %*
set "TEGAKI_EXIT=%ERRORLEVEL%"
popd
echo TEGAKI finished. Review diagnostics above.
pause
exit /b %TEGAKI_EXIT%
