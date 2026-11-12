$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-cab-r4'){throw 'Wrong branch'}
$record=Join-Path $PSScriptRoot 'legend-iconclip-sequence.json'
$state=@{schema=1;pid=$PID;status='build';started_at=(Get-Date -Format o);source_sha=(git rev-parse HEAD).Trim();stage='result-0112-legendiconclip'}
function Save-State {$state.updated_at=Get-Date -Format o;$state | ConvertTo-Json | Set-Content $record -Encoding utf8}
Save-State
try {
  pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/cab-r4/build-0112.ps1 -Label legendiconclip
  if($LASTEXITCODE -ne 0){throw ('Legend build exit '+$LASTEXITCODE)}
  $slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
  foreach($light in @('clear','overcast','dusk')){
    $state.status='capture-'+$light;Save-State
    $output='artifacts/cab-r4/result-0112-legendiconclip/Low-'+$light
    pwsh $slot -Acquire -Owner gpt-cab -PollSeconds 5 -StaleHours 1000000 *> ('artifacts/cab-r4/acquire-legend-iconclip-'+$light+'.log')
    if($LASTEXITCODE -ne 0){throw 'Legend capture slot failed'}
    try {
      pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting $light -Width 1920 -Height 1080 -Cameras 'cab-driver,cab-dash' -OutputDir $output
      $code=$LASTEXITCODE
    } finally {
      pwsh $slot -Release -Owner gpt-cab
      git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
    if($code -ne 0){throw ('Legend capture exit '+$code)}
    Add-Content artifacts/cab-r4/STATUS.md ('Zapisano izolowany atlas legend 256 bias -0.75 icon clip 0.28 Low '+$light+': cab-driver/cab-dash. Plastic/Leather bez zmian. To eksperyment czytelności, nie pełny gate budżetów.')
    git add -f -- artifacts/cab-r4/STATUS.md
    git commit -m ('WIP cab r4: capture isolated Low legend atlas '+$light)
  }
  $state.status='finished';$state.finished_at=Get-Date -Format o;Save-State
} catch {
  $state.failed_phase=$state.status;$state.status='stopped';$state.error=$_.Exception.Message;Save-State
  throw
}

