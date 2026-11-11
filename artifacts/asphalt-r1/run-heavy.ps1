param(
    [Parameter(Mandatory)][ValidateSet('World','Materials','FocusedTests','Fidelity','PhysicsGate3','Compare','Inventory','WheelMetrics')][string]$Stage,
    [string]$Label = 'candidate', [string[]]$Tests = @(), [string]$Only = '', [switch]$EndOfRound
)
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$env:PYTHONUNBUFFERED = '1'
$slotScript = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$owner = (& git branch --show-current).Trim()
if ($LASTEXITCODE -ne 0 -or -not $owner) { throw 'Cannot determine heavy-slot branch owner' }
if ($Stage -eq 'FocusedTests') {
    if ($Tests.Count -eq 0) { throw 'Specify individual test files' }
    foreach ($file in $Tests) {
        if ($file -notmatch '^tests/(gis|physics|gate3)/.+\.py$') { throw 'Only individual test files are allowed mid-round' }
    }
}
if ($Stage -eq 'PhysicsGate3' -and -not $EndOfRound) { throw 'Use -EndOfRound for the complete physics/gate3 suite' }
$log = "artifacts/asphalt-r1/$Label-$Stage.log"
& pwsh $slotScript -Acquire -Pool heavy -Owner $owner -PollSeconds 5
if ($LASTEXITCODE -ne 0) { throw 'Heavy slot acquisition failed' }
$code = 1
try {
    switch ($Stage) {
        'World' { & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> $log }
        'Materials' {
            $argsForBuild = @('run','--project','tools/worldgen','python','art-source/world/materials/_src/build_all.py')
            if ($Only) { $argsForBuild += @('--only',$Only) }
            & uv @argsForBuild *> $log
        }
        'FocusedTests' { & uv run --project tools/worldgen python -m pytest @Tests -q *> $log }
        'Fidelity' { & uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region bialystok-industrial-c --art "artifacts/asphalt-r1/$Label-fidelity" *> $log }
        'PhysicsGate3' { & uv run --project tools/worldgen python -m pytest tests/physics tests/gate3 -q *> $log }
        'Compare' { & uv run --project tools/worldgen python artifacts/asphalt-r1/compare.py --after $Label *> $log }
        'WheelMetrics' { & uv run --project tools/worldgen python artifacts/asphalt-r1/wheel_contrast.py --after $Label *> $log }
        'Inventory' { & uv run --project tools/worldgen python artifacts/asphalt-r1/patch_inventory.py *> $log }
    }
    $code = $LASTEXITCODE
} finally {
    & pwsh $slotScript -Release -Pool heavy -Owner $owner
}
Add-Content artifacts/asphalt-r1/STATUS.md "$(Get-Date -Format o): heavy $Stage owner=$owner exit=$code; log $log. Slot zwolniony po zakończeniu procesu."
git add -f artifacts/asphalt-r1/STATUS.md
git commit -m "wip(asphalt): checkpoint heavy $Stage $Label"
exit $code

