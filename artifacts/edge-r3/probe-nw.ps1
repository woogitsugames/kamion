$ErrorActionPreference = 'Stop'
$root = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $root
$slot = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Pool unity -Owner gpt-edge -PollSeconds 2 -StaleHours 100000
if ($LASTEXITCODE -ne 0) { throw 'Unity slot failed' }
try {
    & pwsh scripts/visual-qa.ps1 -Scene WorldC_High -Tier High -Lighting clear `
        -Gate3 "$PSScriptRoot/proof-nw-probe.json" -Cameras edge-nw-ground -OutputDir "$PSScriptRoot/nw-probe"
    if ($LASTEXITCODE -ne 0) { throw 'NW diagnostic probe failed' }
} finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slot -Release -Pool unity -Owner gpt-edge -StaleHours 100000
}
