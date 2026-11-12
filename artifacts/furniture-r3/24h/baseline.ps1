$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r3/24h'
# Baseline generated after the main merge, before any r3 furniture implementation.
& pwsh "$ev/heavy-step.ps1" -Step pbr -Phase before
if($LASTEXITCODE -ne 0){throw 'Baseline PBR failed'}
& pwsh "$ev/heavy-step.ps1" -Step world -Phase before
if($LASTEXITCODE -ne 0){throw 'Baseline world failed'}
& pwsh "$ev/heavy-step.ps1" -Step geometry -Phase before
if($LASTEXITCODE -ne 0){throw 'Baseline protected geometry failed'}
& pwsh "$ev/unity-step.ps1" -Step import -Phase before
if($LASTEXITCODE -ne 0){throw 'Baseline import failed'}
foreach($tier in @('Low','High')){
    foreach($light in @('clear','overcast')){
        & pwsh "$ev/unity-step.ps1" -Step render -Phase before -Tier $tier -Lighting $light
        if($LASTEXITCODE -ne 0){throw "Baseline capture failed:$tier $light"}
    }
}
