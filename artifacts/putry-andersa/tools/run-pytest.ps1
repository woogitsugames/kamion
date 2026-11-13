# ADR 0146: pytest tests/gis + tests/gate3 under the heavy slot.
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
& pwsh -NoProfile -File $slot -Acquire -Pool heavy -Owner claude-putry-andersa -PollSeconds 5
try {
    Push-Location $root
    & uv run --project tools/worldgen python -m pytest tests/gis tests/gate3 tests/physics/test_swept_path_gate3.py -q -p no:cacheprovider *> (Join-Path $root 'artifacts\putry-andersa\logs\pytest.log')
    "pytest exit=$LASTEXITCODE" | Tee-Object (Join-Path $root 'artifacts\putry-andersa\logs\pytest.done')
} finally {
    & pwsh -NoProfile -File $slot -Release -Pool heavy -Owner claude-putry-andersa
    Pop-Location
}
