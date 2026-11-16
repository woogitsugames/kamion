# rail-dk65-s22 (s23): dk65-06 start moved past the roundabout (owner decision): re-import the tile (the importer bakes
# the catalog startS as the scene spawn), render the start cameras, EditMode StartClearanceTests.
# Waits for the tykocin r3b unity chain (one Unity process per project directory). Status: logs/start06.status
$ErrorActionPreference = 'Continue'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$A = 'artifacts/rail-dk65-s22'; $L = "$A/logs"; $st = "$L/start06.status"; $main = 'C:\Users\matma\Documents\Claude\kamion'
$Owner = 'rail-dk65-s22-start06'
function Step($name, [scriptblock]$b) {
  "$name start $(Get-Date -Format s)" | Add-Content $st
  $global:LASTEXITCODE = 0
  & $b *> "$L/$name.log"
  "$name exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
}
while (-not (Select-String -Path "$L/regen-unity.status" -Pattern '^UNITY DONE r3b ' -Quiet)) { Start-Sleep 30 }
while (Test-Path "$main\artifacts\locks\PHONE_RUN") { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Pool unity -Owner $Owner | Out-Null
Step 'start06-import' { pwsh scripts/import-region.ps1 -Region dk65-06 }
Step 'start06-vqa-high' { pwsh scripts/visual-qa.ps1 -Scene 'World_dk65-06' -Tier High -Lighting clear -Width 1920 -Height 1080 -OutputDir "$A/vqa/start06/dk65-06/High" }
Step 'start06-editmode' { pwsh scripts/test.ps1 -Platform EditMode -Filter StartClearanceTests }
pwsh scripts/unity-slot.ps1 -Release -Pool unity -Owner $Owner | Out-Null
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
"START06 DONE $(Get-Date -Format s)" | Add-Content $st
