@echo off
rem Python generatora swiata (s25): bazowy CPython uv + pakiety ze starego venv agent-a492e5af856a32ed3.
rem Smart App Control od 27.11 22:10 blokuje .venv\Scripts\python.exe; bazowy interpreter i stare DLL pakietow dzialaja.
rem PYTHONPATH: site-packages starego venv + biezacy katalog (worktree) + to, co ustawil wywolujacy.
set "PYTHONPATH=C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\agent-a492e5af856a32ed3\tools\worldgen\.venv\Lib\site-packages;%CD%;%PYTHONPATH%"
"C:\Users\matma\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe" %*
