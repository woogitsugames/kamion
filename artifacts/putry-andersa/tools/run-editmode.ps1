# ADR 0146: EditMode tests under a Unity slot, side effects restored.
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
& pwsh -NoProfile -File $slot -Acquire -Owner claude-putry-andersa -PollSeconds 20
try {
    Push-Location $root
    & pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode *> (Join-Path $root 'artifacts\putry-andersa\logs\editmode.log')
    "editmode exit=$LASTEXITCODE" | Tee-Object (Join-Path $root 'artifacts\putry-andersa\logs\editmode.done')
} finally {
    & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -NoProfile -File $slot -Release -Owner claude-putry-andersa
    Pop-Location
}
