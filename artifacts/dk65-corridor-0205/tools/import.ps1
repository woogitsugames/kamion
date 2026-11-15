# ADR 0205: import dk65-01 into Unity + visual-qa Low/High clear. Status: logs/chain.status (end = IMPORT DONE)
param([switch]$SkipImport, [string]$Tag = 'r1')
$ErrorActionPreference = 'Continue'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$A = 'artifacts/dk65-corridor-0205'; $L = "$A/logs"; $st = "$L/chain.status"; $o = 'dk65-corridor-0205'
$phone = 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN'
function Unity($name, [scriptblock]$b) {
  while (Test-Path $phone) { Start-Sleep 60 }
  pwsh scripts/unity-slot.ps1 -Acquire -Owner $o | Out-Null
  "$name start $(Get-Date -Format s)" | Add-Content $st
  & $b *> "$L/$name.log"
  "$name exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
  pwsh scripts/unity-slot.ps1 -Release -Owner $o | Out-Null
  git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
}
if (-not $SkipImport) { Unity "import-$Tag" { pwsh scripts/import-region.ps1 -Region dk65-01 } }
Unity "vqa-low-$Tag" { pwsh scripts/visual-qa.ps1 -Scene World_dk65-01 -Tier Low -Lighting clear -Width 1920 -Height 1080 -OutputDir "$A/$Tag/Low-clear" }
Unity "vqa-high-$Tag" { pwsh scripts/visual-qa.ps1 -Scene World_dk65-01 -Tier High -Lighting clear -Width 1920 -Height 1080 -OutputDir "$A/$Tag/High-clear" }
"IMPORT DONE $Tag $(Get-Date -Format s)" | Add-Content $st
