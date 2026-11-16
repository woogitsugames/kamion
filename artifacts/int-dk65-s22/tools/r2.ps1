# int-dk65-s22 r2: rebuild knyszyn (compact roundabout, ADR 0218 5c), then - only after the r1 unity chain has
# finished (one Unity per project directory) - import + visual-qa Low/High of knyszyn with tag r2.
param([string]$Tag = "r3")
$ErrorActionPreference = 'Continue'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$L = 'artifacts/int-dk65-s22/logs'
pwsh -NoProfile -File artifacts/int-dk65-s22/tools/chain.ps1 -Mode world -Tiles knyszyn -Tag $Tag
"r2 waits for UNITY DONE r1 $(Get-Date -Format s)" | Add-Content "$L/chain-unity.status"
while (-not ((Test-Path "$L/chain-unity.status") -and (Get-Content "$L/chain-unity.status" | Where-Object { $_ -match '^UNITY DONE r1 ' }))) { Start-Sleep 60 }
pwsh -NoProfile -File artifacts/int-dk65-s22/tools/chain.ps1 -Mode unity -Tiles knyszyn -Tag $Tag
