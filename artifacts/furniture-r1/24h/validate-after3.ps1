param([int]$GenerationChainPid=91696)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r1/24h'
# Wait for the already running chain; never launch a replacement generator.
if (Get-Process -Id $GenerationChainPid -ErrorAction SilentlyContinue) {
    Wait-Process -Id $GenerationChainPid -ErrorAction SilentlyContinue
}
if (!(Select-String -Path "$ev/STATUS.md" -SimpleMatch 'heavy world after3; sukces=True;')) {
    throw 'The existing after3 generation did not report success. Inspect it before proceeding.'
}
if (!(Test-Path "$ev/build-after3.log")) { throw 'Missing after3 generation log' }
if (Select-String -Path "$ev/build-after3.log" -SimpleMatch 'fallback=True') {
    throw 'Unexpected source fallback in after3 generation'
}
if (Test-Path "$ev/after") { throw 'Final renders already exist; inspect them instead of overwriting evidence' }
& pwsh "$ev/heavy-step.ps1" -Step geometry -Phase after
if ($LASTEXITCODE -ne 0) { throw 'Exported geometry verification failed' }
& pwsh "$ev/unity-step.ps1" -Step import -Phase after
if ($LASTEXITCODE -ne 0) { throw 'After3 import failed' }
foreach ($tier in @('Low','High')) {
    foreach ($light in @('overcast','clear')) {
        & pwsh "$ev/unity-step.ps1" -Step render -Phase after -Tier $tier -Lighting $light
        if ($LASTEXITCODE -ne 0) { throw "Render failed: $tier $light" }
    }
}
& pwsh "$ev/unity-step.ps1" -Step sbs-sign -Phase after -Tier High -Lighting overcast
if ($LASTEXITCODE -ne 0) { throw 'Sign reference render failed' }
& pwsh "$ev/heavy-step.ps1" -Step compare -Phase after3
if ($LASTEXITCODE -ne 0) { throw 'All-camera comparison failed' }
Write-Output 'After3 validation products ready for visual review; no quality PASS inferred.'
