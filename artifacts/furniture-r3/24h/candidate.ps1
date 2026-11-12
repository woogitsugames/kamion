param([Parameter(Mandatory=$true)][int]$FocusedPid)
$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r3/24h'
$focused=Get-CimInstance Win32_Process -Filter "ProcessId=$FocusedPid"
if($focused){
    if($focused.CommandLine -notmatch 'furniture-r3/24h/heavy-step.ps1.*-Step focused'){throw 'Unexpected focused test process'}
    Wait-Process -Id $FocusedPid -ErrorAction SilentlyContinue
}
# Do not share a same-owner heavy slot with the focused process, or build after a failed contract.
$test="$ev/pytest-test_furniture_shelters_0120-candidate1.log"
if(!(Test-Path $test) -or !(Select-String -LiteralPath $test -Pattern '^10 passed in ')){
    throw 'Focused shelter contracts have not passed; inspect the retained log before generation'
}
& pwsh "$ev/heavy-step.ps1" -Step world -Phase after1
if($LASTEXITCODE -ne 0){throw 'Candidate world failed'}
& pwsh "$ev/heavy-step.ps1" -Step geometry -Phase after
if($LASTEXITCODE -ne 0){throw 'Protected geometry comparison failed'}
& pwsh "$ev/unity-step.ps1" -Step import -Phase after1
if($LASTEXITCODE -ne 0){throw 'Candidate import failed'}
foreach($tier in @('Low','High')){
    foreach($light in @('clear','overcast')){
        & pwsh "$ev/unity-step.ps1" -Step render -Phase after -Tier $tier -Lighting $light
        if($LASTEXITCODE -ne 0){throw "Candidate capture failed:$tier $light"}
    }
}
