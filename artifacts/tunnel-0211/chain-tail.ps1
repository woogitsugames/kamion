# ADR 0211: remaining steps after import+vqa: EditMode -> sweeps -> pytest tests/gis
param([string]$Tag = 'r4', [string]$From = 'editmode')
$ErrorActionPreference = 'Continue'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\tunnel-0211'
$n = 'tunnel-0211'
$st = "artifacts/$n/chain-$Tag.status"
if ($From -eq 'editmode') {
    while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
    pwsh scripts/unity-slot.ps1 -Acquire -Owner $n | Out-Null
    "editmode(tail) start $(Get-Date -Format s)" | Add-Content $st
    pwsh scripts/test.ps1 -Platform EditMode *> "artifacts/$n/editmode-$Tag-b.log"
    "editmode exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
    pwsh scripts/unity-slot.ps1 -Release -Owner $n | Out-Null
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
tools/worldgen/.venv/Scripts/python.exe "artifacts/$n/tunnel_sweep.py" *> "artifacts/$n/tunnel_sweep-$Tag.txt"
tools/worldgen/.venv/Scripts/python.exe "artifacts/$n/route_sweep.py" *> "artifacts/$n/route_sweep-$Tag.txt"
"sweeps done $(Get-Date -Format s)" | Add-Content $st
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $n | Out-Null
"pytest start $(Get-Date -Format s)" | Add-Content $st
uv run --project tools/worldgen python -m pytest tests/gis -q *> "artifacts/$n/pytest-$Tag.log"
"pytest exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner $n | Out-Null
"TAIL DONE $(Get-Date -Format s)" | Add-Content $st
