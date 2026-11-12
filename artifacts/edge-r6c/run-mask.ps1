# ADR 0141 diagnostic: magenta mask of one renderer for a few cameras (Low clear), under a Unity slot.
param([string]$Mask = 'FarSkyline', [string]$Cameras = 'edge-south,sbs-g3-b-297817221966185,sbs-g3-b-150280503737744', [string]$Name = 'mask', [string]$Rq = '')
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
& pwsh -NoProfile -File $slot -Acquire -Owner claude-edge-r6c
try {
    Push-Location $root
    $extra = @(); if ($Rq) { $extra = @('-Rq', $Rq) }
    & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -Width 1280 -Height 960 -Gate3 Data/Regions/bialystok-industrial-c/sbs_cameras.json -Cameras $Cameras -Mask $Mask -OutputDir "artifacts/edge-r6c/$Name" @extra
    "mask exit=$LASTEXITCODE"
} finally {
    & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -NoProfile -File $slot -Release -Owner claude-edge-r6c
    Pop-Location
}
