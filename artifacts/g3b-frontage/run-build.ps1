# Rebuilds the region (heavy slot) and logs to artifacts/g3b-frontage/<Log>.
param([string]$Log = 'build-world-0.log')
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
& pwsh -NoProfile -File $slot -Acquire -Pool heavy -Owner claude-g3b-frontage -PollSeconds 2
try {
    Push-Location $root
    & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> (Join-Path $PSScriptRoot $Log)
    "build exit=$LASTEXITCODE"
} finally {
    & pwsh -NoProfile -File $slot -Release -Pool heavy -Owner claude-g3b-frontage
    Pop-Location
}
