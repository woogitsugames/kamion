# ADR 0146: WorldC control cameras Low + High (clear) under a Unity slot, side effects restored.
param([string]$Name = 'after4')
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$log = Join-Path $root "artifacts\putry-andersa\logs\control-$Name.log"
& pwsh -NoProfile -File $slot -Acquire -Owner claude-putry-andersa -PollSeconds 20
try {
    Push-Location $root
    foreach ($tier in 'Low', 'High') {
        & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting clear -OutputDir (Join-Path $root "artifacts\putry-andersa\$Name\control\$tier-clear") *>> $log
        "control $tier exit=$LASTEXITCODE" | Tee-Object -Append $log
    }
    "done" | Set-Content (Join-Path $root "artifacts\putry-andersa\logs\control-$Name.done")
} finally {
    & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -NoProfile -File $slot -Release -Owner claude-putry-andersa
    Pop-Location
}
