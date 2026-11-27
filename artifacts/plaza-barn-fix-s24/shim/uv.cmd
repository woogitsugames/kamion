@echo off
rem garden-trees-s24: Smart App Control blocks python.exe of a NEW venv; scripts call "uv run --project tools/worldgen [python] script args".
rem This shim runs the script with the interpreter of worktree a492 (allowed) and PYTHONPATH = this worktree.
pwsh -NoProfile -File "%~dp0uv-shim.ps1" %*
exit /b %ERRORLEVEL%
