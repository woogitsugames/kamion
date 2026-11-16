# c-regen3-s23: detached chain 20-regen -> 40-unity -> 50-pytest. Each step has its own status file with exit= lines;
# this file only records the order. The budget gate lives in 20-regen (no regen.done) and again in 40-unity (never -Force).
$ErrorActionPreference = 'Continue'
$t = $PSScriptRoot; $wt = (Resolve-Path "$t\..\..\..").Path; Set-Location $wt
$s = "$wt\artifacts\c-regen3-s23\chain.status"
function L($m) { "$m $(Get-Date -Format s)" | Add-Content $s }
L 'chain start'
pwsh -NoProfile -File "$t\20-regen.ps1"; L "20-regen exit=$LASTEXITCODE"
if (-not (Test-Path "$wt\artifacts\c-regen3-s23\regen\regen.done")) { L 'STOP: regen not green (build_world or budget) - report to the lead'; exit 1 }
pwsh -NoProfile -File "$t\40-unity.ps1"; L "40-unity exit=$LASTEXITCODE"
pwsh -NoProfile -File "$t\50-pytest.ps1"; L "50-pytest exit=$LASTEXITCODE"
L 'CHAIN END'
