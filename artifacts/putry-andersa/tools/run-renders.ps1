# ADR 0146: Low overcast + clear SBS renders and photo|before / photo|after pairs (sbs-low-pairs takes the Unity slot
# itself), then the native-focal probe of 494288. Before = main at ADR 0143 (artifacts/sbs-poses-r3/after in main).
param([string]$Name = 'after', [switch]$SkipPreflight)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$log = Join-Path $root "artifacts\putry-andersa\logs\renders-$Name.log"
Push-Location $root
try {
    $a = @('-NoProfile', '-File', 'scripts/sbs-low-pairs.ps1', '-OutputRoot', "artifacts/putry-andersa/$Name",
           '-SlotOwner', 'claude-putry-andersa', '-Before', 'C:\Users\matma\Documents\Claude\kamion\artifacts\sbs-poses-r3\after')
    if ($SkipPreflight) { $a += '-SkipPreflight' }
    & pwsh @a *> $log
    "pairs exit=$LASTEXITCODE" | Tee-Object -Append $log
    & pwsh -NoProfile -File $slot -Acquire -Owner claude-putry-andersa -PollSeconds 20
    try {
        foreach ($light in 'overcast', 'clear') {
            & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting $light -Width 1280 -Height 960 `
                -Gate3 (Join-Path $root 'artifacts\putry-andersa\data\probe_cameras.json') -Cameras 'sbs-p146-494288-native' `
                -OutputDir (Join-Path $root "artifacts\putry-andersa\$Name\probe\Low-$light") *>> $log
            "probe $light exit=$LASTEXITCODE" | Tee-Object -Append $log
        }
    } finally {
        & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
        & pwsh -NoProfile -File $slot -Release -Owner claude-putry-andersa
    }
    "done" | Set-Content (Join-Path $root "artifacts\putry-andersa\logs\renders-$Name.done")
} finally { Pop-Location }
