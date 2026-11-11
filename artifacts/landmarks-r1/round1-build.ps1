$ErrorActionPreference = 'Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
foreach ($step in @('Materials','World','FocusedGIS')) {
    $log = "artifacts/landmarks-r1/round1-$($step.ToLowerInvariant()).log"
    & pwsh artifacts/landmarks-r1/heavy-step.ps1 -Step $step -Log $log
    if ($LASTEXITCODE -ne 0) { throw "$step failed; stop before import" }
}
$world = Get-Content "$PSScriptRoot/round1-world.log" -Raw
if ($world.Contains('fallback=True') -or -not $world.Contains('instance landmark_fire_station_jrg2')) {
    throw 'World uses a fallback or the fire station hero was not applied'
}
& pwsh artifacts/landmarks-r1/unity-step.ps1 -Step Import
if ($LASTEXITCODE -ne 0) { throw 'Round 1 import failed' }
& pwsh artifacts/landmarks-r1/unity-step.ps1 -Step Capture -Phase round1
exit $LASTEXITCODE
