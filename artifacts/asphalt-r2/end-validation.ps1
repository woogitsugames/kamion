param([Parameter(Mandatory)][int]$AfterCompareProcessId)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if ((& git branch --show-current).Trim() -ne 'gpt-asphalt-r2') { throw 'Wrong branch for final r2 validation' }
$process=Get-CimInstance Win32_Process -Filter "ProcessId=$AfterCompareProcessId"
if($process -and ($process.Name -ne 'pwsh.exe' -or $process.CommandLine -notmatch '\sartifacts/asphalt-r2/run-heavy.ps1\s+-Stage\s+Compare\s+-Label\s+candidate')) { throw 'Unexpected process to await' }
if($process){Write-Output "Awaiting own Compare wrapper PID $AfterCompareProcessId"; Wait-Process -Id $AfterCompareProcessId -ErrorAction SilentlyContinue}
# This checkpoint is written after Compare's Python exits, before its final WIP commit;
# Wait-Process above also ensures that commit finished before any further git operation.
$status=Get-Content artifacts/asphalt-r2/STATUS.md -Raw
if($status -notmatch 'heavy Compare owner=gpt-asphalt-r2 exit=0; log artifacts/asphalt-r2/candidate-Compare.log'){throw 'Compare did not finish successfully'}
$results=[ordered]@{branch='gpt-asphalt-r2';started=(Get-Date -Format o);compare=0}
& pwsh artifacts/asphalt-r2/run-gis.ps1 -EndOfRound -Label candidate-final
$results.gis_exit=$LASTEXITCODE
$results | ConvertTo-Json | Set-Content artifacts/asphalt-r2/validation-progress.json
& pwsh artifacts/asphalt-r2/run-heavy.ps1 -Stage PhysicsGate3 -Label candidate-final -EndOfRound
$results.physics_gate3_exit=$LASTEXITCODE
$results | ConvertTo-Json | Set-Content artifacts/asphalt-r2/validation-progress.json
& pwsh artifacts/asphalt-r2/run-heavy.ps1 -Stage Fidelity -Label candidate-final
$results.fidelity_exit=$LASTEXITCODE
$results.finished=(Get-Date -Format o)
$results | ConvertTo-Json | Set-Content artifacts/asphalt-r2/validation-progress.json
Add-Content artifacts/asphalt-r2/STATUS.md "$(Get-Date -Format o): Końcowa sekwencja testów zakończona; surowe exit codes w validation-progress.json. Wyniki wymagają odczytania przed końcowym REPORT i publikacją."
git add -f artifacts/asphalt-r2/STATUS.md artifacts/asphalt-r2/validation-progress.json
git commit -m 'wip(asphalt): checkpoint complete end-round validation sequence' 2> artifacts/asphalt-r2/git-checkpoint-warnings.log
Write-Output ($results | ConvertTo-Json)
if($results.gis_exit -ne 0 -or $results.fidelity_exit -ne 0){exit 1}
exit 0
