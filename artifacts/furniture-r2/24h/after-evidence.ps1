$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r2/24h'
& pwsh "$ev/after-images.ps1"
if ($LASTEXITCODE -ne 0) { throw 'Standard images or counters failed; inspect before resuming' }
foreach ($tier in @('Low','High')) {
    & pwsh "$ev/unity-step.ps1" -Step night-rig -Phase after1 -Tier $tier
    if ($LASTEXITCODE -ne 0) { throw "Controlled real-rig capture failed: $tier" }
}
Write-Output 'Standard and controlled evidence captured; appearance and budgets still require review.'
