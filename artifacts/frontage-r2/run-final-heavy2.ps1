# s13: second heavy pass (after the car_row proto fix): waits until the Unity import of pass 1 has copied the world, then
# build_world -> fidelity -> pytest gis + gate3 (logs *-3.log, status final-heavy2.status).
$us = Join-Path $PSScriptRoot 'final-unity.status'
while (-not ((Test-Path $us) -and (Select-String -Path $us -Pattern '^import done' -Quiet))) { Start-Sleep 15 }
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$st = Join-Path $PSScriptRoot 'final-heavy2.status'
& pwsh -NoProfile -File $slot -Acquire -Pool heavy -Owner claude-frontage-r2-py -PollSeconds 10
try {
    Push-Location $root
    & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> (Join-Path $PSScriptRoot 'build-world-3.log')
    "build exit=$LASTEXITCODE $(Get-Date -Format HH:mm:ss)" | Add-Content $st
    & uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region bialystok-industrial-c *> (Join-Path $PSScriptRoot 'fidelity-3.log')
    "fidelity exit=$LASTEXITCODE $(Get-Date -Format HH:mm:ss)" | Add-Content $st
    & uv run --project tools/worldgen pytest tests/gis tests/gate3 -q *> (Join-Path $PSScriptRoot 'pytest-gis-gate3-3.log')
    "pytest exit=$LASTEXITCODE $(Get-Date -Format HH:mm:ss)" | Add-Content $st
} finally { & pwsh -NoProfile -File $slot -Release -Pool heavy -Owner claude-frontage-r2-py; Pop-Location; "heavy2 done $(Get-Date -Format HH:mm:ss)" | Add-Content $st }
