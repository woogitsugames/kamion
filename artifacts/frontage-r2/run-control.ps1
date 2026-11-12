# Renders the ADR 0126 control cameras (Data/Regions/.../g3b_frontage_cameras.json) into artifacts/frontage-r2/<Name>/control-<Tier>-<Lighting>.
param([string]$Name = 'after', [string]$Tier = 'Low', [string]$Lighting = 'overcast')
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$cameraFile = Join-Path $root 'Data/Regions/bialystok-industrial-c/g3b_frontage_cameras.json'
$ids = ((Get-Content $cameraFile -Raw | ConvertFrom-Json).cameras.id -join ',')
$out = Join-Path $root "artifacts\frontage-r2\$Name\control-$Tier-$Lighting"
New-Item -ItemType Directory -Force $out | Out-Null
& pwsh -NoProfile -File $slot -Acquire -Owner claude-frontage-r2 -PollSeconds 5
try {
    Push-Location $root
    & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier $Tier -Lighting $Lighting -Width 1280 -Height 960 -Gate3 $cameraFile -Cameras $ids -OutputDir $out
    "control render exit=$LASTEXITCODE -> $out"
} finally {
    & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -NoProfile -File $slot -Release -Owner claude-frontage-r2
    Pop-Location
}
