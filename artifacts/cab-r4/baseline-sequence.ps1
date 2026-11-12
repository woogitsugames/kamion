param([switch]$ReuseWorld,[switch]$PreparePhoto)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-cab-r4'){throw 'Wrong branch'}
$env:UV_PROJECT_ENVIRONMENT='.venv-cab'
$record=Join-Path $PSScriptRoot 'baseline-sequence.json'
$state=@{schema=1;pid=$PID;status='world';started_at=(Get-Date -Format o);source_sha=(git rev-parse HEAD).Trim()}
function Save-State { $state.updated_at=Get-Date -Format o; $state | ConvertTo-Json | Set-Content $record -Encoding utf8 }
function Check-Code([string]$label) { if($LASTEXITCODE -ne 0){throw ($label+' exit '+$LASTEXITCODE)} }
Save-State
try {
  if($ReuseWorld){
    $world=Get-Content artifacts/cab-r4/job-World-20261112-113440-63340.json -Raw | ConvertFrom-Json
    if($world.status -ne 'finished' -or $world.exit_code -ne 0){throw 'No successful prior World'}
    git diff --quiet $world.source_sha -- tools/worldgen
    Check-Code 'World generator source changed'
    if((Get-FileHash Data/Regions/bialystok-industrial-c/generated/world_manifest.json).Hash -ne (Get-FileHash artifacts/cab-r4/world-cli/world_manifest.json).Hash){throw 'World manifest changed'}
    $state.reused_world_receipt='job-World-20261112-113440-63340.json';Save-State
  } else {
    pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/cab-r4/heavy-0112.ps1 -Job World -Log artifacts/cab-r4/build-world-r4.log
    Check-Code 'World'
    if(Select-String -LiteralPath artifacts/cab-r4/build-world-r4.log -SimpleMatch 'fallback=True' -Quiet){throw 'World used fallback=True'}
    New-Item -ItemType Directory -Force artifacts/cab-r4/world-cli | Out-Null
    Copy-Item Data/Regions/bialystok-industrial-c/generated/world_manifest.json artifacts/cab-r4/world-cli/world_manifest.json
    Add-Content artifacts/cab-r4/STATUS.md 'World r4 exit 0, brak literalnego fallback=True. Snapshot manifestu zapisany; zachować produkty do końcowego GIS. Następny krok import baseline.'
    git add -f -- artifacts/cab-r4/STATUS.md artifacts/cab-r4/world-cli/world_manifest.json
    git commit -m 'WIP cab r4: preserve fresh world before baseline import'
  }
  $state.status='import';Save-State
  $slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
  $heavy=$false;$unity=$false
  $guard=[System.Threading.Mutex]::new($false,'Local\kamion-cab-heavy-gpt-cab-r4')
  if(-not $guard.WaitOne(0)){ $guard.Dispose();throw 'Other own heavy job active' }
  try {
    pwsh $slot -Acquire -Pool heavy -Owner gpt-cab-r4 -PollSeconds 1 -StaleHours 1000000 *> artifacts/cab-r4/acquire-heavy-import.log
    Check-Code 'Heavy acquire';$heavy=$true
    if($PreparePhoto){
      uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --only asphalt_detail_photo *> artifacts/cab-r4/photo-layer-repair.log
      Check-Code 'Photo layer preparation'
      if(Select-String -LiteralPath artifacts/cab-r4/photo-layer-repair.log -SimpleMatch 'SKIP asphalt_detail_photo' -Quiet){throw 'Photo layer still skipped'}
    }
    pwsh $slot -Acquire -Owner gpt-cab -PollSeconds 5 -StaleHours 1000000 *> artifacts/cab-r4/acquire-unity-import.log
    Check-Code 'Unity acquire';$unity=$true
    pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/import-region.ps1 -Region bialystok-industrial-c *> artifacts/cab-r4/baseline-import.log
    Check-Code 'Import'
    if(Select-String -LiteralPath artifacts/cab-r4/baseline-import.log -SimpleMatch 'SKIP asphalt_detail_photo' -Quiet){throw 'Incomplete photo layer input'}
  } finally {
    if($unity){pwsh $slot -Release -Owner gpt-cab}
    if($heavy){pwsh $slot -Release -Pool heavy -Owner gpt-cab-r4}
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    $guard.ReleaseMutex();$guard.Dispose()
  }
  Add-Content artifacts/cab-r4/STATUS.md 'Import baseline exit 0; build_all/cc0_fetch i Unity objęte slotami heavy oraz Unity, zwolnionymi w finally. Następny krok przebudowa kabiny i świeże kadry.'
  git add -f -- artifacts/cab-r4/STATUS.md
  git commit -m 'WIP cab r4: import current main world for baseline'
  $state.status='truck-build';Save-State
  pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/cab-r4/build-0112.ps1 -Label baseline
  Check-Code 'Truck build'
  $state.status='cab-capture';Save-State
  pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/cab-r4/capture-0112.ps1 -Stage baseline
  Check-Code 'Cab capture'
  $state.status='route-capture';Save-State
  pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/cab-r4/route-0112.ps1 -Stage baseline
  Check-Code 'Route capture'
  $state.status='finished';$state.finished_at=Get-Date -Format o;Save-State
} catch {
  $state.failed_phase=$state.status;$state.status='stopped';$state.error=$_.Exception.Message;Save-State
  throw
}

