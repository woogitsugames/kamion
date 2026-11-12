param([Parameter(Mandatory)][int]$AfterProcessId)
$ErrorActionPreference = 'Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
# A queued Acquire with the same owner is reentrant. Wait for the actual predecessor to exit first.
while (Get-Process -Id $AfterProcessId -ErrorAction SilentlyContinue) { Start-Sleep -Seconds 5 }
$metrics = Get-Content "$PSScriptRoot/sky-grade-metrics.json" -Raw | ConvertFrom-Json
if ($metrics.results.Count -ne 18) { throw 'Missing complete sky-grade analysis; do not start another heavy job' }
$xml = [xml](Get-Content "$PSScriptRoot/tests/editmode-final.xml" -Raw)
if ($xml.'test-run'.failed -ne '0' -or $xml.'test-run'.passed -ne '276') { throw 'Final EditMode276 must pass first' }
foreach($tier in @('Low','High')) {
    if (@(Get-ChildItem "$PSScriptRoot/final-route-v2/$tier-night" -Filter '*.png').Count -ne 67) { throw 'Incomplete final night cameras' }
}
& pwsh "$PSScriptRoot/run-heavy.ps1" -Task GisFinal -RoundEnd
exit $LASTEXITCODE
