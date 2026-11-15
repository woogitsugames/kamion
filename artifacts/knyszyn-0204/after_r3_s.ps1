Set-Location $PSScriptRoot\..\..
$A = "artifacts/knyszyn-0204"
pwsh -NoProfile -File "$A/chain_world.ps1" -Region knyszyn-s
while (-not (Select-String -Path "$A/full_knyszyn_r3.status" -Pattern 'FULL DONE' -Quiet)) { Start-Sleep 30 }
pwsh -NoProfile -File "$A/chain_unity.ps1" -Region knyszyn-s -Tag r2 -Tiers Low,High
