param(
    [Parameter(Mandatory)][ValidateSet('World','GisFile','GisFinal')][string]$Job,
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
pwsh $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 5 -StaleHours 1000000
if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu heavy.' }
try {
    $env:UV_PROJECT_ENVIRONMENT='.venv-cab'
    switch ($Job) {
        'World' { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> $Log }
        'GisFile' { uv run --project tools/worldgen python -m pytest $TestFile -q *> $Log }
        'GisFinal' { uv run --project tools/worldgen python -m pytest tests/gis -q *> $Log }
    }
    $code=$LASTEXITCODE
}
finally { pwsh $slot -Release -Pool heavy -Owner $owner }
exit $code
