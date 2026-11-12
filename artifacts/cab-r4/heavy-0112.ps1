param(
    [Parameter(Mandatory)][ValidateSet('World','Fidelity','GisFile','GisFinal','Images','MaterialPrep')][string]$Job,
    [string]$TestFile,
    [string]$Log
)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$owner=(git branch --show-current).Trim()
if ($owner -notmatch '^gpt-cab-r\d+$') { throw 'Uruchom tylko na gałęzi rundy cab.' }
if ($Job -eq 'GisFile' -and (-not (Test-Path $TestFile -PathType Leaf) -or $TestFile -notmatch '^tests[/\\](gis|physics|gate3)[/\\].+\.py$')) { throw 'W trakcie rundy wybierz pojedynczy plik testów.' }
if (-not $Log) { $Log="$PSScriptRoot/heavy-$Job-$(Get-Date -Format yyyyMMdd-HHmmss).log" }
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$guard=[System.Threading.Mutex]::new($false,"Local\kamion-cab-heavy-$owner")
if (-not $guard.WaitOne(0)) { $guard.Dispose(); throw 'Inne własne zadanie heavy jest już aktywne. Nie pozyskuj ani nie zwalniaj jego slotu.' }
$receipt=Join-Path $PSScriptRoot ("job-{0}-{1}-{2}.json" -f $Job,(Get-Date -Format yyyyMMdd-HHmmss),$PID)
$acquireLog=[IO.Path]::ChangeExtension($receipt,'.acquire.log')
$run=@{schema=1;owner=$owner;job=$Job;pid=$PID;source_sha=(git rev-parse HEAD).Trim();status='waiting';queued_at=(Get-Date -Format o);log=$Log;acquire_log=$acquireLog;exit_code=$null}
$run | ConvertTo-Json | Set-Content -LiteralPath $receipt -Encoding utf8
try {
  pwsh $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 1 -StaleHours 1000000 *> $acquireLog
  if ($LASTEXITCODE -ne 0) { throw "Nie uzyskano slotu heavy; pełny log: $acquireLog" }
  $run.status='running'; $run.started_at=Get-Date -Format o
  $run | ConvertTo-Json | Set-Content -LiteralPath $receipt -Encoding utf8
  try {
    $env:UV_PROJECT_ENVIRONMENT='.venv-cab'
    switch ($Job) {
        'MaterialPrep' { uv run --project tools/worldgen python artifacts/cab-r4/prepare-material-candidate.py *> $Log }
        'Images' { uv run --project tools/worldgen python artifacts/cab-r4/review-sheets.py *> $Log }
        'World' { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> $Log }
        'Fidelity' { uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region bialystok-industrial-c --art artifacts/cab-r4/fidelity *> $Log }
        'GisFile' { uv run --project tools/worldgen python -m pytest $TestFile -q *> $Log }
        'GisFinal' { uv run --project tools/worldgen python -m pytest tests/gis -q *> $Log }
    }
    $code=$LASTEXITCODE
    $run.exit_code=$code; $run.status='finished'; $run.finished_at=Get-Date -Format o
    $run | ConvertTo-Json | Set-Content -LiteralPath $receipt -Encoding utf8
  }
  finally { pwsh $slot -Release -Pool heavy -Owner $owner }
}
catch {
  $run.status='wrapper-error'; $run.error=$_.Exception.Message; $run.finished_at=Get-Date -Format o
  $run | ConvertTo-Json | Set-Content -LiteralPath $receipt -Encoding utf8
  throw
}
finally { $guard.ReleaseMutex(); $guard.Dispose() }
exit $code


