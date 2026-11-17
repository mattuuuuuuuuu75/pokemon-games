@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "GIT_EXE=git"
where git >nul 2>&1
if errorlevel 1 (
  for /d %%D in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do (
    if exist "%%D\resources\app\git\cmd\git.exe" set "GIT_EXE=%%D\resources\app\git\cmd\git.exe"
  )
)

echo Publishing update to GitHub Pages (https://mattuuuuuuuuu75.github.io/pokemon-games/)...
"%GIT_EXE%" add -A
"%GIT_EXE%" commit -m "Update pokemon-games content"
"%GIT_EXE%" push origin main

echo Done! GitHub Pages will reflect the update within ~30-60 seconds.
pause
