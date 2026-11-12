param([int]$WorldProcessId=0)
$ErrorActionPreference='Stop'
if($WorldProcessId -gt 0){
    $worldProcess=Get-Process -Id $WorldProcessId -ErrorAction Stop
    $null=$worldProcess.Handle
    Write-Output "Waiting for own world process $WorldProcessId"
    $worldProcess.WaitForExit()
    if($worldProcess.ExitCode -ne 0){throw "World process failed: $($worldProcess.ExitCode)"}
} else {
    $receipt=Get-Content artifacts/sbs-r2/world-completed.json -Raw | ConvertFrom-Json
    $logHash=(Get-FileHash artifacts/sbs-r2/build-world.log).Hash.ToLowerInvariant()
    $worldHash=(Get-FileHash Data/Regions/bialystok-industrial-c/generated/world_manifest.json).Hash.ToLowerInvariant()
    if($receipt.exit_code -ne 0 -or $receipt.log_sha256 -ne $logHash -or $receipt.world_manifest_sha256 -ne $worldHash){throw 'Completed world receipt differs from current files'}
}
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
