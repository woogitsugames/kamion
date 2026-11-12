param(
    [Parameter(Mandatory)]
    [ValidateSet('World','WorldWithFocusedGIS','Materials','FinalGIS','FocusedGIS','PhysicsGate3','Fidelity')][string]$Step,
    [string]$Only = 'fire_station',
    [string]$Tiers = 'Medium',
    [string]$TestFile = 'tests/gis/test_viaduct_underdeck.py',
    [string]$Log = 'artifacts/landmarks-r3/heavy-step.log'
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
& pwsh $slotScript -Acquire -Pool heavy -Owner $owner -PollSeconds 2 -StaleHours 876000
if ($LASTEXITCODE -ne 0) { throw 'Heavy slot acquisition failed' }
try {
    switch ($Step) {
        'WorldWithFocusedGIS' {
            & uv run --project tools/worldgen python -m pytest tests/gis/test_viaduct_underdeck.py -q *> "$Log.focused"
            if($LASTEXITCODE -ne 0){throw "Focused underdeck tests failed, log: $Log.focused"}
            Add-Content -Encoding utf8 "$PSScriptRoot/STATUS.md" "`nKrok 7: pojedynczy plik test_viaduct_underdeck.py dla wariantu weather zakończył się powodzeniem; dokładna liczba i czas w $Log.focused. Pod tym samym slotem heavy rozpoczyna się kolejno generator, bez równoległego Pythona tej sesji."
            & git add -f artifacts/landmarks-r3/STATUS.md
            & git commit -m 'wip(landmarks): testy pojedynczego pliku przed generacją weather'
            if($LASTEXITCODE -ne 0){throw 'Focused checkpoint failed'}
            & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> $Log
        }
        'World' { & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> $Log }
        'Materials' {
            if ($Only.Split(',') -contains 'fire_station') {
                & uv run --project tools/worldgen python art-source/world/materials/_src/sets_fire_station.py --alpha --layout *> "$Log.alpha"
                if ($LASTEXITCODE -ne 0) { throw "Hero atlas preparation failed, log: $Log.alpha" }
            }
            & uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --only $Only --tier $Tiers *> $Log
        }
        'FinalGIS' { & uv run --project tools/worldgen python -m pytest tests/gis -q *> $Log }
        'PhysicsGate3' { & uv run --project tools/worldgen python -m pytest tests/physics tests/gate3 -q *> $Log }
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

