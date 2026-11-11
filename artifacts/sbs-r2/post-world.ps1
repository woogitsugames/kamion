param([Parameter(Mandatory)][int]$WorldProcessId)
$ErrorActionPreference='Stop'
$worldProcess=Get-Process -Id $WorldProcessId -ErrorAction Stop
$null=$worldProcess.Handle
Write-Output "Waiting for own world process $WorldProcessId"
$worldProcess.WaitForExit()
if($worldProcess.ExitCode -ne 0){throw "World process failed: $($worldProcess.ExitCode)"}
Write-Output 'World finished successfully; starting sequential file checks.'
foreach($test in @('test_sbs_report','test_sbs_gate3','test_sbs_photometry')){
    pwsh -NoProfile -File artifacts/sbs-r2/run-heavy.ps1 -Task TestFile -TestFile "tests/gis/$test.py" *> "artifacts/sbs-r2/$test.log"
    if($LASTEXITCODE -ne 0){throw "Focused test failed: $test"}
    Write-Output "$test OK"
}
pwsh -NoProfile -File artifacts/sbs-r2/run-heavy.ps1 -Task Fidelity *> artifacts/sbs-r2/fidelity.log
if($LASTEXITCODE -ne 0){throw 'Fidelity failed'}
Write-Output 'Fidelity OK'
pwsh -NoProfile -File artifacts/sbs-r2/recompose-history.ps1 *> artifacts/sbs-r2/recompose-history.log
if($LASTEXITCODE -ne 0){throw 'Historical remeasurement failed'}
Write-Output 'Historical remeasurement OK'
