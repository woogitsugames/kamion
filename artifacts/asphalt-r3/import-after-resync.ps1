param([Parameter(Mandatory)][int]$ProducerProcessId)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if ((& git branch --show-current).Trim() -ne 'gpt-asphalt-r3') { throw 'Wrong round' }
$producer=Get-CimInstance Win32_Process -Filter "ProcessId=$ProducerProcessId"
if($producer){
 if($producer.Name -ne 'pwsh.exe' -or $producer.CommandLine -notmatch '" artifacts/asphalt-r3/resync-baseline\.ps1$'){throw 'Unexpected producer'}
 "Waiting for own post-0131 producer PID $ProducerProcessId before import"
 Wait-Process -Id $ProducerProcessId -ErrorAction SilentlyContinue
}
$receipt=Get-Content artifacts/asphalt-r3/baseline-producer-progress.json -Raw|ConvertFrom-Json
if(-not $receipt.complete -or $receipt.world_exit -ne 0 -or $receipt.resync_merge -ne 'e5eb5902'){throw 'Fresh producer failed or incomplete'}
if(Test-Path artifacts/asphalt-r3/baseline-import-progress.json){
 $previous=Get-Content artifacts/asphalt-r3/baseline-import-progress.json -Raw|ConvertFrom-Json
 if($previous.exit -eq 0 -and [datetimeoffset]$previous.started_at -gt [datetimeoffset]$receipt.finished_at){throw 'Fresh import already recorded; inspect it instead of duplicating'}
}
& pwsh artifacts/asphalt-r3/import-baseline.ps1
exit $LASTEXITCODE
