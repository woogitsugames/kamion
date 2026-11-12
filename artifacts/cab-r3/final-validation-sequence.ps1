param([int]$FidelityPid=18764)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-cab-r3'){throw 'Wrong branch'}
$receipt=Join-Path $PSScriptRoot 'job-Fidelity-20261112-102447-18764.json'
$record=Join-Path $PSScriptRoot 'final-validation-sequence.json'
$state=@{schema=1;pid=$PID;fidelity_pid=$FidelityPid;status='waiting-fidelity';started_at=(Get-Date -Format o)}
$state | ConvertTo-Json | Set-Content $record -Encoding utf8
try {
  $process=Get-Process -Id $FidelityPid -ErrorAction SilentlyContinue
  if($process){Wait-Process -Id $FidelityPid}
  $result=Get-Content $receipt -Raw | ConvertFrom-Json
  if($result.status -ne 'finished' -or $result.exit_code -ne 0){throw ('Fidelity not successful: '+$result.status+' exit '+$result.exit_code)}
  if((git branch --show-current).Trim() -ne 'gpt-cab-r3'){throw 'Branch changed'}
  $state.status='gis-queued';$state.fidelity_finished_at=$result.finished_at
  $state | ConvertTo-Json | Set-Content $record -Encoding utf8
  pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/cab-r3/heavy-0112.ps1 -Job GisFinal -Log artifacts/cab-r3/gis-final-r3.log
  $state.gis_exit_code=$LASTEXITCODE;$state.status='finished';$state.finished_at=Get-Date -Format o
  $state | ConvertTo-Json | Set-Content $record -Encoding utf8
} catch {
  $state.status='stopped';$state.error=$_.Exception.Message;$state.finished_at=Get-Date -Format o
  $state | ConvertTo-Json | Set-Content $record -Encoding utf8
  throw
}
