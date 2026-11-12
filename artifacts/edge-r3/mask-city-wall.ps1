$ErrorActionPreference = 'Stop'
$root = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $root
$slot = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Pool unity -Owner gpt-edge -PollSeconds 2 -StaleHours 100000
if ($LASTEXITCODE -ne 0) { throw 'Unity slot failed' }
try {
    & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast `
        -Gate3 "$PSScriptRoot/proof-cameras.json" `
        -Cameras 'sbs-g3-a-454716650857984,sbs-g3-a-303305168125936,sbs-g3-a-320215796381417' `
        -Mask 'FarField_far_west' -OutputDir "$PSScriptRoot/next-round-review/far-west-mask"
    if ($LASTEXITCODE -ne 0) { throw 'Far-west mask failed' }
} finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slot -Release -Pool unity -Owner gpt-edge -StaleHours 100000
}
