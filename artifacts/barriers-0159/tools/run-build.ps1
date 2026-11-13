# ADR 0159: world rebuild + fidelity under the heavy slot; logs to artifacts/barriers-0159/logs.
param([string]$Tag = '1')
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$logs = Join-Path $root 'artifacts\barriers-0159\logs'
& pwsh -NoProfile -File $slot -Acquire -Pool heavy -Owner barriers-0159 -PollSeconds 15
try {
    Push-Location $root
    & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> (Join-Path $logs "build-world-$Tag.log")
    "build exit=$LASTEXITCODE" | Set-Content (Join-Path $logs "build-world-$Tag.done")
    if ($LASTEXITCODE -eq 0) {
        & uv run --project tools/worldgen python scripts/export-route.py --region bialystok-industrial-c *> (Join-Path $logs "export-route-$Tag.log")
        & uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region bialystok-industrial-c *> (Join-Path $logs "fidelity-$Tag.log")
        "fidelity exit=$LASTEXITCODE" | Add-Content (Join-Path $logs "build-world-$Tag.done")
    }
} finally {
    & pwsh -NoProfile -File $slot -Release -Pool heavy -Owner barriers-0159
    Pop-Location
}
