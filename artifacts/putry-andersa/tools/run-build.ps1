# ADR 0146: rebuilds the region (heavy slot), log to artifacts/putry-andersa/logs/<Log>.
param([string]$Log = 'build-world-1.log')
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
& pwsh -NoProfile -File $slot -Acquire -Pool heavy -Owner claude-putry-andersa -PollSeconds 5
try {
    Push-Location $root
    & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> (Join-Path $root "artifacts\putry-andersa\logs\$Log")
    "build exit=$LASTEXITCODE" | Tee-Object (Join-Path $root "artifacts\putry-andersa\logs\$Log.done")
} finally {
    & pwsh -NoProfile -File $slot -Release -Pool heavy -Owner claude-putry-andersa
    Pop-Location
}
