param([int]$AfterCompareProcessId=0, [ValidatePattern('^candidate[0-9]*$')][string]$Label='candidate2')
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if ((& git branch --show-current).Trim() -ne 'gpt-asphalt-r2') { throw 'Wrong branch for final r2 validation' }
$process=$null
if($AfterCompareProcessId -gt 0){$process=Get-CimInstance Win32_Process -Filter "ProcessId=$AfterCompareProcessId"}
if($process -and ($process.Name -ne 'pwsh.exe' -or $process.CommandLine -notmatch ("\sartifacts/asphalt-r2/run-heavy.ps1\s+-Stage\s+Compare\s+-Label\s+" + [regex]::Escape($Label) + "(?:\s|$)"))) { throw 'Unexpected process to await' }
if($process){Write-Output "Awaiting own Compare wrapper PID $AfterCompareProcessId"; Wait-Process -Id $AfterCompareProcessId -ErrorAction SilentlyContinue}
# This checkpoint is written after Compare's Python exits, before its final WIP commit;
# Wait-Process above also ensures that commit finished before any further git operation.
$status=Get-Content artifacts/asphalt-r2/STATUS.md -Raw
if($status -notmatch ("heavy Compare owner=gpt-asphalt-r2 exit=0; log artifacts/asphalt-r2/" + $Label + "-Compare.log")){throw 'Compare did not finish successfully'}
$comparison=Get-Content "artifacts/asphalt-r2/comparison-$Label.json" -Raw | ConvertFrom-Json
if($comparison.rows -ne 328 -or @($comparison.max_abs_counter_delta.PSObject.Properties | Where-Object Value -ne 0).Count){throw 'Incomplete comparison or counter regressions'}
$results=[ordered]@{branch='gpt-asphalt-r2';label=$Label;started=(Get-Date -Format o);compare=0}
& pwsh artifacts/asphalt-r2/run-gis.ps1 -EndOfRound -Label "$Label-final"
$results.gis_exit=$LASTEXITCODE
$results | ConvertTo-Json | Set-Content artifacts/asphalt-r2/validation-progress.json
& pwsh artifacts/asphalt-r2/run-heavy.ps1 -Stage PhysicsGate3 -Label "$Label-final" -EndOfRound
$results.physics_gate3_exit=$LASTEXITCODE
$results | ConvertTo-Json | Set-Content artifacts/asphalt-r2/validation-progress.json
& pwsh artifacts/asphalt-r2/run-heavy.ps1 -Stage Fidelity -Label "$Label-final"
$results.fidelity_exit=$LASTEXITCODE
& pwsh artifacts/asphalt-r2/run-unity-stage.ps1 -Stage Test -Label "$Label-final" *> "artifacts/asphalt-r2/$Label-final-editmode.log"
$results.editmode_exit=$LASTEXITCODE
$xml=Get-ChildItem artifacts/tests -Filter 'editmode-*.xml' | Sort-Object LastWriteTime | Select-Object -Last 1
if($xml){Copy-Item -LiteralPath $xml.FullName -Destination "artifacts/asphalt-r2/$Label-final-editmode.xml"}
$results.finished=(Get-Date -Format o)
$results | ConvertTo-Json | Set-Content artifacts/asphalt-r2/validation-progress.json
Add-Content artifacts/asphalt-r2/STATUS.md "$(Get-Date -Format o): Końcowa sekwencja testów zakończona; surowe exit codes w validation-progress.json. Wyniki wymagają odczytania przed końcowym REPORT i publikacją."
git add -f artifacts/asphalt-r2/STATUS.md artifacts/asphalt-r2/validation-progress.json
git commit -m 'wip(asphalt): checkpoint complete end-round validation sequence' 2> artifacts/asphalt-r2/git-checkpoint-warnings.log
Write-Output ($results | ConvertTo-Json)
if($results.gis_exit -ne 0 -or $results.fidelity_exit -ne 0 -or $results.editmode_exit -ne 0){exit 1}
exit 0

