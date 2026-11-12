# EditMode tests under a Unity slot.
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
& pwsh -NoProfile -File $slot -Acquire -Owner claude-g3b-lowread
try {
    Push-Location $root
    & pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode *> (Join-Path $PSScriptRoot 'editmode.log')
    "editmode exit=$LASTEXITCODE"
} finally {
    & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -NoProfile -File $slot -Release -Owner claude-g3b-lowread
    Pop-Location
}
