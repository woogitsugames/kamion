# ADR 0141 after merging main: heavy slot (PBR sets, build_world, fidelity, pytest gis+gate3), then Unity slot
# (import-region both tiers, EditMode), then renders "merged" (run-vqa.ps1). Logs: artifacts/edge-r6c/*-merged.log
param([switch]$SkipHeavy)
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$R = 'bialystok-industrial-c'
Push-Location $root
if (-not $SkipHeavy) {
    & pwsh -NoProfile -File $slot -Acquire -Pool heavy -Owner claude-edge-r6c
    $ok = $true
    try {
        & uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py *> (Join-Path $PSScriptRoot 'build_all-merged.log')
        "build_all exit=$LASTEXITCODE"; if ($LASTEXITCODE -ne 0) { $ok = $false }
        if ($ok) {
            & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $R *> (Join-Path $PSScriptRoot 'build_world-merged.log')
            "build_world exit=$LASTEXITCODE"; if ($LASTEXITCODE -ne 0) { $ok = $false }
        }
        if ($ok) {
            & uv run --project tools/worldgen python scripts/export-route.py --region $R *> (Join-Path $PSScriptRoot 'route-merged.log')
            & uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region $R *> (Join-Path $PSScriptRoot 'fidelity-merged.log')
            "fidelity exit=$LASTEXITCODE"
            & uv run --project tools/worldgen python -m pytest tests/gis tests/gate3 -q --no-header -p no:cacheprovider *> (Join-Path $PSScriptRoot 'pytest-merged.log')
            "pytest exit=$LASTEXITCODE"
        }
    } finally { & pwsh -NoProfile -File $slot -Release -Pool heavy -Owner claude-edge-r6c }
    if (-not $ok) { Pop-Location; exit 1 }
}
& pwsh -NoProfile -File $slot -Acquire -Owner claude-edge-r6c
try {
    & pwsh -NoProfile -File scripts/import-region.ps1 -Region $R *> (Join-Path $PSScriptRoot 'import-merged.log')
    "import exit=$LASTEXITCODE"; $imp = $LASTEXITCODE
    if ($imp -eq 0) {
        & pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode *> (Join-Path $PSScriptRoot 'editmode-merged.log')
        "editmode exit=$LASTEXITCODE"
    }
} finally {
    & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -NoProfile -File $slot -Release -Owner claude-edge-r6c
    Pop-Location
}
if ($imp -ne 0) { exit 1 }
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'run-vqa.ps1') -Name merged
