# verify-cloud-c (s21): waits for the dk65 and cworld stages, rebuilds dk65-05 once more (sand seam fix landed after its
# first build), then pytest (parallel, heavy) + cbase -> cunity -> editmode (Unity, serial)
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$L = 'artifacts/verify-cloud-c/logs'; $st = "$L/after.status"
function Done($s) { (Test-Path "$L/$s.status") -and (Select-String -Path "$L/$s.status" -Pattern "STAGE DONE $s" -Quiet) }
"after waiting $(Get-Date -Format s)" | Add-Content $st
while (-not ((Done 'dk65') -and (Done 'cworld'))) { Start-Sleep 30 }
"after go: dk65-05 second pass $(Get-Date -Format s)" | Add-Content $st
pwsh -NoProfile -File artifacts/verify-cloud-c/tools/chain.ps1 -Stage dk65 -Tiles dk65-05
"dk65-05 second pass finished $(Get-Date -Format s)" | Add-Content $st
Start-Process pwsh -ArgumentList '-NoProfile','-File','artifacts/verify-cloud-c/tools/chain.ps1','-Stage','pytest' -WindowStyle Hidden
foreach ($s in 'cbase','cunity','editmode') {
  pwsh -NoProfile -File artifacts/verify-cloud-c/tools/chain.ps1 -Stage $s
  "$s finished $(Get-Date -Format s)" | Add-Content $st
}
"AFTER DONE $(Get-Date -Format s)" | Add-Content $st
