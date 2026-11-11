$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '../..')
$phoneLock = 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN'
function Wait-Phone {
 while (Test-Path $phoneLock) {
  "$(Get-Date -Format o) waiting PHONE_RUN" | Add-Content artifacts/viaduct-r10/unity-queue.log
  Start-Sleep -Seconds 30
 }
}
function Restore-Unity {
 git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
$cameras = 'dk8-under-span,dk8-bearing,dk8-abutment,route-putry-entry-signs,g3b-rondo-putry-approach'
foreach ($tier in @('Low','High')) {
 foreach ($light in @('overcast','clear')) {
  Wait-Phone
  try {
   & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting $light -Gate3 artifacts/viaduct-r10/cameras.json -Cameras $cameras -OutputDir "artifacts/viaduct-r10/before/$tier-$light"
   if ($LASTEXITCODE -ne 0) { throw "baseline render $tier/$light failed" }
  } finally { Restore-Unity }
 }
}
'baseline renders finished' | Add-Content artifacts/viaduct-r10/unity-queue.log

