# verify-cloud-c (s22): successor of after.ps1 without cbase/cunity (#82 superseded by #93, bridge renders not needed).
# waits for STAGE DONE dk65 -> dk65-05 second pass (sand seam fix) -> pytest (parallel) + editmode
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$L = 'artifacts/verify-cloud-c/logs'; $st = "$L/after2.status"
"after2 waiting $(Get-Date -Format s)" | Add-Content $st
while (-not (Select-String -Path "$L/dk65.status" -Pattern 'STAGE DONE dk65' -Quiet)) { Start-Sleep 30 }
Copy-Item "$L/dk65.status" "$L/dk65-pass1.status" -Force
"after2 go: dk65-05 second pass $(Get-Date -Format s)" | Add-Content $st
pwsh -NoProfile -File artifacts/verify-cloud-c/tools/chain.ps1 -Stage dk65 -Tiles dk65-05
"dk65-05 second pass finished $(Get-Date -Format s)" | Add-Content $st
Start-Process pwsh -ArgumentList '-NoProfile','-File','artifacts/verify-cloud-c/tools/chain.ps1','-Stage','pytest' -WindowStyle Hidden
pwsh -NoProfile -File artifacts/verify-cloud-c/tools/chain.ps1 -Stage editmode
"editmode finished $(Get-Date -Format s)" | Add-Content $st
"AFTER2 DONE $(Get-Date -Format s)" | Add-Content $st
