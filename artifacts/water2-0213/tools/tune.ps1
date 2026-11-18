# ADR 0213 shader / colour tuning loop: render the water cameras of the imported scenes (Low + High) and measure.
param([string]$Tag = 't1', [string]$Region = 'dk65-03', [string]$Cams = 'top_water_mid,top_water_seam,water_close_bank,water_bank_mid,water_oblique_east', [string]$Tiers = 'Low,High')
$ErrorActionPreference = 'Continue'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$A = 'artifacts/water2-0213'; $o = 'water2-0213'; $st = "$A/logs/tune.status"
$phone = 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN'
foreach ($t in $Tiers -split ',') {
  while (Test-Path $phone) { Start-Sleep 60 }
  pwsh scripts/unity-slot.ps1 -Acquire -Pool unity -Owner $o | Out-Null
  "$Tag $Region $t start $(Get-Date -Format s)" | Add-Content $st
  pwsh scripts/visual-qa.ps1 -Scene "World_$Region" -Tier $t -Lighting clear -Width 1920 -Height 1080 -Cameras $Cams -OutputDir "$A/tune/$Region/$Tag/$t" *> "$A/logs/tune-$Region-$Tag-$t.log"
  "$Tag $Region $t exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
  pwsh scripts/unity-slot.ps1 -Release -Pool unity -Owner $o | Out-Null
  git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
}
"TUNE DONE $Tag $Region $(Get-Date -Format s)" | Add-Content $st
