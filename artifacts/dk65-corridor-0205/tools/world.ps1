# ADR 0205: build_world + export-route for dk65-01 under the heavy slot. Status: logs/chain.status
$ErrorActionPreference = 'Continue'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$L = 'artifacts/dk65-corridor-0205/logs'; $st = "$L/chain.status"
"world start $(Get-Date -Format s)" | Add-Content $st
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner dk65-corridor-0205 | Out-Null
"heavy slot $(Get-Date -Format s)" | Add-Content $st
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region dk65-01 --context *> "$L/build_world.log"
$bw = $LASTEXITCODE; "build_world exit=$bw $(Get-Date -Format s)" | Add-Content $st
if ($bw -eq 0) {
  uv run --project tools/worldgen python scripts/export-route.py --region dk65-01 *> "$L/export_route.log"
  "export_route exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
}
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner dk65-corridor-0205 | Out-Null
"WORLD DONE $(Get-Date -Format s)" | Add-Content $st
