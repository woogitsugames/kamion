@echo off
pwsh -NoProfile -File "%~dp0uv-shim.ps1" %*
exit /b %ERRORLEVEL%
