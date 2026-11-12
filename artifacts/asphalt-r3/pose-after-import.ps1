param([Parameter(Mandatory)][int]$ImportProcessId)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if ((& git branch --show-current).Trim() -ne 'gpt-asphalt-r3') { throw 'Wrong round' }
$process=Get-CimInstance Win32_Process -Filter "ProcessId=$ImportProcessId"
if($process){
 if($process.Name -ne 'pwsh.exe' -or $process.CommandLine -notmatch '" artifacts/asphalt-r3/import-after-resync\.ps1 -ProducerProcessId 51772$'){throw 'Unexpected import process'}
 "Waiting for own fresh import PID $ImportProcessId before the yard pose trial"
 Wait-Process -Id $ImportProcessId -ErrorAction SilentlyContinue
}
$world=Get-Content artifacts/asphalt-r3/baseline-producer-progress.json -Raw|ConvertFrom-Json
$import=Get-Content artifacts/asphalt-r3/current-import-state.json -Raw|ConvertFrom-Json
$result=Get-Content artifacts/asphalt-r3/baseline-import-progress.json -Raw|ConvertFrom-Json
if(-not $world.complete -or -not $import.complete -or $result.exit -ne 0 -or $import.manifest_sha256 -ne $world.manifest_sha256){throw 'Fresh baseline import did not complete'}
if([datetimeoffset]$result.started_at -le [datetimeoffset]$world.finished_at){throw 'Import predates the current producer'}
$plan=Get-Content artifacts/asphalt-r3/camera-provenance.json -Raw|ConvertFrom-Json
$ids=@($plan.new_yard_probes.ids)
if(-not $ids.Count -or @($ids|Select-Object -Unique).Count -ne $ids.Count){throw 'Invalid pose camera set'}
if(Test-Path artifacts/asphalt-r3/yard-pose-post0131/Low-clear/capture-context.json){throw 'Trial already exists; inspect it before a new uniquely labeled run'}
& pwsh artifacts/asphalt-r3/run-unity-stage.ps1 -Stage Probe -Label yard-pose-post0131 -ProbeTier Low -ProbeLighting clear -Cameras ($ids -join ',')
$code=$LASTEXITCODE
[ordered]@{finished_at=(Get-Date -Format o);import_process_id=$ImportProcessId;exit=$code;ids=$ids;
    next='Inspect all trial PNGs and actual positions. Run audit-yard-poses after the matching SurfaceAudit. Not an accepted full baseline.'
}|ConvertTo-Json -Depth 5|Set-Content artifacts/asphalt-r3/pose-probe-progress.json
Add-Content artifacts/asphalt-r3/STATUS.md "$(Get-Date -Format o): Pierwsza inspekcja placu exit=$code. PNG wymagają obejrzenia, a pozycje sprawdzenia z GLB; nie zatwierdzono pełnego baseline lub dopasowania zdjęcia."
git add -f artifacts/asphalt-r3/STATUS.md artifacts/asphalt-r3/pose-probe-progress.json
git commit -q -m 'wip(asphalt): checkpoint first post-0131 industrial pose trial'
exit $code
