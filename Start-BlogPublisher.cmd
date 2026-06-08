@echo off
setlocal

cd /d "%~dp0"
conda run -n psblog python -m tools.blog_publisher --repo "%~dp0" %*
exit /b %ERRORLEVEL%