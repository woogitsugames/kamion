$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-cab-r4'){throw 'Wrong branch'}
$record=Join-Path $PSScriptRoot 'material-prep-sequence.json'
$state=@{schema=1;pid=$PID;baseline_pid=77492;status='waiting-baseline';started_at=(Get-Date -Format o)}
function Save-State {$state.updated_at=Get-Date -Format o;$state | ConvertTo-Json | Set-Content $record -Encoding utf8}
Save-State
try {
  $baseline=Get-Content artifacts/cab-r4/baseline-sequence.json -Raw | ConvertFrom-Json
  if($baseline.pid -ne 77492){throw 'Unexpected baseline identity'}
  if(Get-Process -Id 77492 -ErrorAction SilentlyContinue){Wait-Process -Id 77492}
  $baseline=Get-Content artifacts/cab-r4/baseline-sequence.json -Raw | ConvertFrom-Json
  if($baseline.status -ne 'finished'){throw ('Baseline not complete: '+$baseline.status)}
  if((git branch --show-current).Trim() -ne 'gpt-cab-r4'){throw 'Branch changed'}
  $state.status='material-prep';Save-State
  pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/cab-r4/heavy-0112.ps1 -Job MaterialPrep -Log artifacts/cab-r4/material-prep.log
  if($LASTEXITCODE -ne 0){throw ('MaterialPrep exit '+$LASTEXITCODE)}
  if(-not (Select-String -LiteralPath artifacts/cab-r4/material-prep.log -SimpleMatch 'CAB_MATERIAL_PREP_RESULT: OK' -Quiet)){throw 'Missing material verification marker'}
  $state.status='finished';$state.finished_at=Get-Date -Format o;Save-State
  Add-Content artifacts/cab-r4/STATUS.md 'Baseline kompletny; MaterialPrep exit 0 i marker OK. Odtworzenie 12 map oraz kandydat offline zweryfikowane według material-prep/verification.json. Mapy/config gry niezmienione. Następny krok obejrzeć normal-map-comparison i baseline, dopiero potem integrować wybrany wariant.'
  git add -f -- artifacts/cab-r4/STATUS.md artifacts/cab-r4/material-prep-sequence.json artifacts/cab-r4/material-prep/verification.json
  git commit -m 'WIP cab r4: preserve verified offline material candidate'
} catch {
  $state.status='stopped';$state.error=$_.Exception.Message;Save-State
  throw
}
