# s13 final: build_world -> fidelity -> pytest gis + gate3 under ONE heavy slot (owner claude-frontage-r2-py).
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$st = Join-Path $PSScriptRoot 'final-heavy.status'
& pwsh -NoProfile -File $slot -Acquire -Pool heavy -Owner claude-frontage-r2-py -PollSeconds 10
try {
    Push-Location $root
    & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> (Join-Path $PSScriptRoot 'build-world-2.log')
    "build exit=$LASTEXITCODE $(Get-Date -Format HH:mm:ss)" | Add-Content $st
    & uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region bialystok-industrial-c *> (Join-Path $PSScriptRoot 'fidelity.log')
    "fidelity exit=$LASTEXITCODE $(Get-Date -Format HH:mm:ss)" | Add-Content $st
    & uv run --project tools/worldgen pytest tests/gis tests/gate3 -q *> (Join-Path $PSScriptRoot 'pytest-gis-gate3.log')
    "pytest exit=$LASTEXITCODE $(Get-Date -Format HH:mm:ss)" | Add-Content $st
} finally { & pwsh -NoProfile -File $slot -Release -Pool heavy -Owner claude-frontage-r2-py; Pop-Location; "heavy done $(Get-Date -Format HH:mm:ss)" | Add-Content $st }
