Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$L = 'artifacts/verify-cloud-c/logs'; $st = "$L/cfid.status"
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner verify-cloud-c-cfid | Out-Null
"c-fidelity start $(Get-Date -Format s)" | Add-Content $st
uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c --art artifacts/verify-cloud-c/pr82/fidelity *> "$L/c-fidelity.log"
"c-fidelity exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner verify-cloud-c-cfid | Out-Null
"STAGE DONE cfid $(Get-Date -Format s)" | Add-Content $st
