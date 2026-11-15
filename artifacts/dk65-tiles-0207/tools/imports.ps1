# ADR 0207: imports + vqa (serial, one Unity per project): 03, 04 Low; 05 Low+High. Waits for the world chain of 05.
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$st = 'artifacts/dk65-tiles-0207/logs/chain.status'
pwsh -NoProfile -File artifacts/dk65-tiles-0207/tools/chain.ps1 -Tiles dk65-03,dk65-04 -Tag r2 -NoWorld
while (-not (Select-String -Path $st -Pattern 'world-dk65-05-r2 exit' -Quiet)) { Start-Sleep 20 }
pwsh -NoProfile -File artifacts/dk65-tiles-0207/tools/chain.ps1 -Tiles dk65-05 -Tag r2 -NoWorld -High
