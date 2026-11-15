param([string]$Region)
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot\..\..
$A = "artifacts/knyszyn-0204"; $st = "$A/world_$Region.status"
"start $(Get-Date -Format s)" | Set-Content $st
$env:PYTHONUNBUFFERED = '1'
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner "knyszyn-0204-$Region" | Out-Null
"slot $(Get-Date -Format s)" | Add-Content $st
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $Region --context *> "$A/build_world_$Region.log"
"build_world exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
uv run --project tools/worldgen python scripts/export-route.py --region $Region *> "$A/export_route_$Region.log"
"export_route exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
uv run --project tools/worldgen tools/worldgen/qa_report.py --region $Region *> "$A/qa_report_$Region.log"
"qa_report exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner "knyszyn-0204-$Region" | Out-Null
"DONE $(Get-Date -Format s)" | Add-Content $st
