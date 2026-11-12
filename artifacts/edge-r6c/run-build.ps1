# ADR 0141: regenerate the world after merging main (heavy pool slot), then pytest gis+gate3 under the same slot.
param([switch]$SkipBuild, [switch]$SkipTests)
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
& pwsh -NoProfile -File $slot -Acquire -Pool heavy -Owner claude-edge-r6c
try {
    Push-Location $root
    if (-not $SkipBuild) {
        & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> (Join-Path $PSScriptRoot 'build_world-merged.log')
        "build_world exit=$LASTEXITCODE"
        if ($LASTEXITCODE -ne 0) { exit 1 }
    }
    if (-not $SkipTests) {
        & uv run --project tools/worldgen python -m pytest tests/gis tests/gate3 -q --no-header -p no:cacheprovider *> (Join-Path $PSScriptRoot 'pytest-merged.log')
        "pytest exit=$LASTEXITCODE"
    }
} finally {
    & pwsh -NoProfile -File $slot -Release -Pool heavy -Owner claude-edge-r6c
    Pop-Location
}
