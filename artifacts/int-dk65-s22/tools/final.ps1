# int-dk65-s22 closing checks: full pytest tests/gis (heavy slot), then EditMode (unity slot). Status: logs/final.status
$ErrorActionPreference = 'Continue'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$L = 'artifacts/int-dk65-s22/logs'; $st = "$L/final.status"; $main = 'C:\Users\matma\Documents\Claude\kamion'
function Step($name, [scriptblock]$b) {
  "$name start $(Get-Date -Format s)" | Add-Content $st
  $global:LASTEXITCODE = 0
  & $b *> "$L/$name.log"
  "$name exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
}
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner int-dk65-s22 | Out-Null
Step 'pytest-gis' { uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider }
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner int-dk65-s22 | Out-Null
while (Test-Path "$main\artifacts\locks\PHONE_RUN") { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Pool unity -Owner int-dk65-s22 | Out-Null
Step 'editmode' { pwsh scripts/test.ps1 -Platform EditMode }
pwsh scripts/unity-slot.ps1 -Release -Pool unity -Owner int-dk65-s22 | Out-Null
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
"FINAL DONE $(Get-Date -Format s)" | Add-Content $st
