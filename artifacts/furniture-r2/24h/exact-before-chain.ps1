param([switch]$Resume)
$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
foreach ($light in @('clear','overcast','dusk')) {
    if ($Resume -and (Test-Path "artifacts/furniture-r2/24h/exact-before/Low-$light/validation.json")) {
        & uv run --project tools/worldgen python artifacts/furniture-r2/24h/verify_exact_stats.py before Low $light
        if ($LASTEXITCODE -ne 0) { throw "Existing capture is not valid: $light" }
        continue
    }
    & pwsh artifacts/furniture-r2/24h/exact-stats.ps1 -Phase before -Tier Low -Lighting $light
    if ($LASTEXITCODE -ne 0) { throw "Before exact capture failed: $light" }
}
Write-Output 'Exact Low baseline saved and checked against every frozen frame.'
