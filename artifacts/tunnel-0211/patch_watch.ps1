Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\tunnel-0211'
while (-not (Select-String -Path artifacts/tunnel-0211/chain-r1.status -Pattern 'export_route start|STOP|FAILED' -Quiet)) { Start-Sleep 20 }
tools/worldgen/.venv/Scripts/python.exe artifacts/tunnel-0211/patch_cams.py *> artifacts/tunnel-0211/patch_cams.log
