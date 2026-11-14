# ADR 0205: pytest tests/gis (heavy slot) + EditMode (unity slot). Status: logs/chain.status (end = POST DONE)
$ErrorActionPreference = 'Continue'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$L = 'artifacts/dk65-corridor-0205/logs'; $st = "$L/chain.status"; $o = 'dk65-corridor-0205'
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $o | Out-Null
"pytest start $(Get-Date -Format s)" | Add-Content $st
uv run --project tools/worldgen python -m pytest tests/gis -q -x --deselect tests/gis/test_road_fidelity.py::test_report_not_stale *> "$L/pytest-gis.log"
"pytest exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner $o | Out-Null
while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Owner $o | Out-Null
"editmode start $(Get-Date -Format s)" | Add-Content $st
pwsh scripts/test.ps1 -Platform EditMode *> "$L/editmode.log"
"editmode exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
pwsh scripts/unity-slot.ps1 -Release -Owner $o | Out-Null
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
"POST DONE $(Get-Date -Format s)" | Add-Content $st
