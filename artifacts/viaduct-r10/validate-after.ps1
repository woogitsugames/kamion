$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '../..')
$phoneLock = 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN'
function Wait-Phone {
 while (Test-Path $phoneLock) { Start-Sleep -Seconds 30 }
}
function Restore-Unity {
 git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
# Keep the copied Unity scene for the baseline and wait for the stable GIS run:
# its fixture also rebuilds world chunks, so do not import concurrently with it.
while ($true) {
 $before = Test-Path artifacts/viaduct-r10/unity-queue.log
 if ($before) { $before = Select-String artifacts/viaduct-r10/unity-queue.log -Pattern '^baseline renders finished$' -Quiet }
 $gis = Test-Path artifacts/viaduct-r10/final-gis-r3.log
 if ($gis) { $gis = Select-String artifacts/viaduct-r10/final-gis-r3.log -Pattern '^\d+ passed.*in ' -Quiet }
 if ($before -and $gis) { break }
 Start-Sleep -Seconds 30
}
. ./scripts/env.ps1
# All Medium PBR sets were copied from main during preparation; validate that
# direct import cannot silently use a missing-texture fallback.
$spec = Get-Content art-source/world/materials/materials_spec.json -Raw | ConvertFrom-Json
foreach ($set in $spec.sets.PSObject.Properties) {
 $files = $set.Value.files.Medium
 if ($files) {
  foreach ($name in $files.files) {
   if (!(Test-Path "art-source/world/materials/$($files.dir)/$name")) { throw "Missing PBR $($set.Name)/$name" }
  }
 }
}
Wait-Phone
try {
 $log = Join-Path $RepoRoot 'artifacts/viaduct-r10/import.log'
 $code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.World.Import.RegionImporter.ImportBatch','-region','bialystok-industrial-c','-tiers','Low,High','-materialTier','Medium')
 if ($code -ne 0 -or !(Select-String $log -Pattern 'IMPORT_RESULT: OK' -Quiet)) { throw "Import failed ($code): $log" }
} finally { Restore-Unity }
foreach ($tier in @('Low','High')) {
 foreach ($light in @('overcast','clear')) {
  Wait-Phone
  try {
   & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting $light -Gate3 artifacts/viaduct-r10/cameras.json -Cameras 'dk8-under-span,dk8-bearing,dk8-abutment,route-putry-entry-signs,g3b-rondo-putry-approach' -OutputDir "artifacts/viaduct-r10/after/$tier-$light"
   if ($LASTEXITCODE -ne 0) { throw "after render $tier/$light failed" }
  } finally { Restore-Unity }
 }
}
Wait-Phone
try {
 & pwsh scripts/test.ps1 -Platform EditMode
 if ($LASTEXITCODE -ne 0) { throw 'EditMode failed; inspect artifacts/tests' }
} finally { Restore-Unity }
'after render and EditMode finished' | Add-Content artifacts/viaduct-r10/unity-queue.log
