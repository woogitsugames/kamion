$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
foreach ($light in @('clear','overcast','dusk')) {
    & pwsh artifacts/furniture-r2/24h/exact-stats.ps1 -Phase before -Tier Low -Lighting $light
    if ($LASTEXITCODE -ne 0) { throw "Before exact capture failed: $light" }
}
Write-Output 'Exact Low baseline saved and checked against every frozen frame.'
