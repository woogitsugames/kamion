param(
    [Parameter(Mandatory)]
    [ValidateSet('World','Materials','FinalGIS','FocusedGIS','Fidelity')][string]$Step,
    [string]$Only = 'fire_station',
    [string]$Tiers = 'Medium',
    [string]$TestFile = 'tests/gis/test_fire_station_r7.py',
    [string]$Log = 'artifacts/landmarks-r1/heavy-step.log'
)
$ErrorActionPreference = 'Stop'
$wt = Split-Path (Split-Path $PSScriptRoot)
Set-Location $wt
# Main owns the updated pool implementation. Do not overwrite Claude's script
# in this round's source tree merely to obtain the new infrastructure command.
$slotScript = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$owner = (& git branch --show-current).Trim()
if ($owner -notlike 'gpt-landmarks-r*') { throw 'Unexpected branch for a landmarks heavy job' }
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:PYTHONUNBUFFERED = '1'
$env:KAMION_BLENDER = 'C:\Users\matma\AppData\Local\Programs\Blender4.2\blender-4.2.9-windows-x64\blender.exe'
& pwsh $slotScript -Acquire -Pool heavy -Owner $owner -PollSeconds 10 -StaleHours 876000
if ($LASTEXITCODE -ne 0) { throw 'Heavy slot acquisition failed' }
try {
    switch ($Step) {
        'World' { & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> $Log }
        'Materials' {
            if ($Only.Split(',') -contains 'fire_station') {
                & uv run --project tools/worldgen python art-source/world/materials/_src/sets_fire_station.py --alpha --layout *> "$Log.alpha"
                if ($LASTEXITCODE -ne 0) { throw "Hero atlas preparation failed, log: $Log.alpha" }
            }
            & uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --only $Only --tier $Tiers *> $Log
        }
        'FinalGIS' { & uv run --project tools/worldgen python -m pytest tests/gis -q *> $Log }
        'FocusedGIS' {
            if ($TestFile -notmatch '^tests/gis/test_[A-Za-z0-9_]+\.py$') { throw 'Focused test must name one test file' }
            & uv run --project tools/worldgen python -m pytest $TestFile -q *> $Log
        }
        'Fidelity' { & uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region bialystok-industrial-c *> $Log }
    }
    $code = $LASTEXITCODE
    if ($code -ne 0) { throw "$Step failed ($code), log: $Log" }
} finally {
    & pwsh $slotScript -Release -Pool heavy -Owner $owner
}
