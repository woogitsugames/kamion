param([string]$Region, [string]$Tag = 'r1', [switch]$SkipImport, [string]$Tiers = 'Low')
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot\..\..
$A = "artifacts/knyszyn-0204"; $st = "$A/unity_${Region}_$Tag.status"
"start $(Get-Date -Format s)" | Set-Content $st
while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Owner knyszyn-0204 | Out-Null
"slot $(Get-Date -Format s)" | Add-Content $st
if (-not $SkipImport) {
  pwsh scripts/import-region.ps1 -Region $Region *> "$A/import_${Region}_$Tag.log"
  "import exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
}
foreach ($t in $Tiers.Split(',')) {
  $sc = if ($t -eq 'High') { "World_${Region}_High" } else { "World_$Region" }
  pwsh scripts/visual-qa.ps1 -Scene $sc -Tier $t -Lighting overcast -TimeFrames 3 -OutputDir "$A/vqa/$Region/$Tag-$t" *> "$A/vqa_${Region}_${Tag}_$t.log"
  "vqa $t exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
}
pwsh scripts/unity-slot.ps1 -Release -Owner knyszyn-0204 | Out-Null
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
"DONE $(Get-Date -Format s)" | Add-Content $st
