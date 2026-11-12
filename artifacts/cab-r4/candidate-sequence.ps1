$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-cab-r4'){throw 'Wrong branch'}
$record=Join-Path $PSScriptRoot 'candidate-sequence.json'
$state=@{schema=1;pid=$PID;status='build';started_at=(Get-Date -Format o);source_sha=(git rev-parse HEAD).Trim();stage='result-0112-hp15'}
function Save-State {$state.updated_at=Get-Date -Format o;$state | ConvertTo-Json | Set-Content $record -Encoding utf8}
Save-State
try {
  pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/cab-r4/build-0112.ps1 -Label hp15
  if($LASTEXITCODE -ne 0){throw ('Candidate build exit '+$LASTEXITCODE)}
  $state.status='capture';Save-State
  pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/cab-r4/capture-0112.ps1 -Stage result-0112-hp15
  if($LASTEXITCODE -ne 0){throw ('Candidate capture exit '+$LASTEXITCODE)}
  $state.status='route';Save-State
  pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/cab-r4/route-0112.ps1 -Stage result-0112-hp15
  if($LASTEXITCODE -ne 0){throw ('Candidate route exit '+$LASTEXITCODE)}
  $state.status='finished';$state.finished_at=Get-Date -Format o;Save-State
} catch {
  $state.failed_phase=$state.status;$state.status='stopped';$state.error=$_.Exception.Message;Save-State
  throw
}
