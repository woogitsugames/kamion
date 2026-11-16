# rail-dk65-s22: chain.ps1 for the given regions, then pytest (rail, then the whole tests/gis) under the heavy slot.
# pwsh artifacts/rail-dk65-s22/tools/chain-tests.ps1 -Regions dw671-tykocin-01 -Tag r2 [-SkipChain]
param([string[]]$Regions, [string]$Tag = 'r2', [switch]$SkipChain)
$ErrorActionPreference = "Continue"
$wt = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
Set-Location $wt
$art = Join-Path $wt 'artifacts/rail-dk65-s22'
$log = Join-Path $art "logs/tests-$Tag.status"
if (-not $SkipChain) { & (Join-Path $PSScriptRoot 'chain.ps1') -Regions $Regions -Tag $Tag }
$owner = 'rail-dk65-s22'
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $owner | Out-Null
foreach ($t in @(@('rail', @('tests/gis', '-k', 'rail')), @('gis', @('tests/gis')))) {
    "pytest-$($t[0]) start $(Get-Date -Format s)" | Add-Content $log
    uv run --project tools/worldgen python -m pytest @($t[1]) -q -p no:cacheprovider *> (Join-Path $art "logs/$Tag-pytest-$($t[0]).log")
    "pytest-$($t[0]) exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $log
}
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner $owner | Out-Null
"TESTS DONE $(Get-Date -Format s)" | Add-Content $log
