# Final cycle: one heavy slot for build_world + fidelity + full GIS suite; after the build the Unity part
# (import -> SBS Low overcast + clear -> EditMode) starts in parallel. Writes all-<Tag>.done at the end.
param([string]$Name = 'after', [string]$Tag = '2')
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$unity = $null
& pwsh -NoProfile -File $slot -Acquire -Pool heavy -Owner claude-g3b-r2 -PollSeconds 5
try {
    Push-Location $root
    & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> (Join-Path $PSScriptRoot "build-world-$Tag.log")
    $b = $LASTEXITCODE
    "build exit=$b"
    if ($b -eq 0) {
        $unity = Start-Process pwsh -PassThru -WindowStyle Hidden -ArgumentList @('-NoProfile', '-File', (Join-Path $PSScriptRoot 'run-unity-2.ps1'), '-Name', $Name, '-Tag', $Tag)
        & uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region bialystok-industrial-c *> (Join-Path $PSScriptRoot 'fidelity.log')
        "fidelity exit=$LASTEXITCODE"
        & uv run --project tools/worldgen pytest tests/gis tests/gate3 -q -p no:cacheprovider *> (Join-Path $PSScriptRoot 'pytest-gis.log')
        "pytest exit=$LASTEXITCODE"
    }
} finally {
    & pwsh -NoProfile -File $slot -Release -Pool heavy -Owner claude-g3b-r2
    Pop-Location
}
if ($unity) { $unity.WaitForExit() }
'done' | Set-Content (Join-Path $PSScriptRoot "all-$Tag.done")
