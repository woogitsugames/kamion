param(
    [ValidateSet('world','pbr','gis','physics','focused')] [string]$Step,
    [string]$Phase='after',
    [string]$TestFile='tests/gis/test_furniture_0120.py'
)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../..").Path
Set-Location $root
$ev='artifacts/furniture-r1/24h'
$owner=(& git branch --show-current).Trim()
if ($owner -notmatch '^gpt-furniture-r\d+$') { throw 'Not an owned furniture round branch' }
# Use the owning main copy: this worktree predates the newly introduced heavy pool.
$slotScript='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
& pwsh $slotScript -Acquire -Pool heavy -Owner $owner -StaleHours 876000 -PollSeconds 10
if ($LASTEXITCODE -ne 0) { throw 'Could not acquire heavy slot' }
$ok=$false
try {
    switch ($Step) {
        'world' { & uv run --project tools/worldgen python -u tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> "$ev/build-$Phase.log" }
        'pbr' { & uv run --project tools/worldgen python -u art-source/world/materials/_src/build_all.py *> "$ev/pbr-$Phase.log" }
        'gis' { & uv run --project tools/worldgen python -m pytest tests/gis -q *> "$ev/pytest-gis-final.log" }
        'physics' { & uv run --project tools/worldgen python -m pytest tests/physics tests/gate3 -q *> "$ev/pytest-physics-gate3.log" }
        'focused' {
            if ($TestFile -notmatch '^tests/gis/test_furniture[^/\\]*\.py$') { throw 'Use one owned furniture test file during the round' }
            & uv run --project tools/worldgen python -m pytest $TestFile -q *> "$ev/pytest-focused.log"
        }
    }
    $code=$LASTEXITCODE
    $ok=$code -eq 0
} finally {
    & pwsh $slotScript -Release -Pool heavy -Owner $owner
    Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): heavy $Step $Phase; sukces=$ok; slot $owner zwolniony. NASTĘPNY KROK: sprawdzić log i kontynuować walidację rundy."
    git add -f "$ev/STATUS.md" "$ev/heavy-step.ps1"
    git commit -m "wip(furniture): checkpoint heavy $Step $Phase"
}
if (!$ok) { throw "Heavy $Step failed ($code); inspect evidence log" }
