$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r2/24h'
& pwsh "$ev/baseline-dusk.ps1"
if ($LASTEXITCODE -ne 0) { throw 'Dusk baseline failed; do not activate candidate' }
& pwsh "$ev/heavy-step.ps1" -Step geometry -Phase before
if ($LASTEXITCODE -ne 0) { throw 'Protected baseline capture failed' }
Write-Output 'Day/dusk baseline and protected geometry saved; inspect before activating candidate.'
