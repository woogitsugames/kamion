# fidelity report refresh + full GIS test suite under one heavy slot.
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
& pwsh -NoProfile -File $slot -Acquire -Pool heavy -Owner claude-frontage-r2-py -PollSeconds 10
try {
    Push-Location $root
    & uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region bialystok-industrial-c *> (Join-Path $PSScriptRoot 'fidelity.log')
    "fidelity exit=$LASTEXITCODE"
    & uv run --project tools/worldgen pytest tests/gis -q *> (Join-Path $PSScriptRoot 'pytest-gis.log')
    "pytest exit=$LASTEXITCODE"
} finally { & pwsh -NoProfile -File $slot -Release -Pool heavy -Owner claude-frontage-r2-py; Pop-Location }
