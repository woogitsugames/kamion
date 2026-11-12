# Renders selected SBS cameras (4:3 or 16:9 photo aspect taken from sbs_references.json) under a Unity slot.
# Usage: run-cams.ps1 -Name diag -Cameras sbs-g3-b-494288258686575[,..] [-Lighting overcast] [-Extra @('-NoGlass')]
param([string]$Name = 'diag', [string]$Cameras, [string]$Tier = 'Low', [string]$Lighting = 'overcast', [string[]]$Extra = @(), [string]$Sub = '')
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$cameraFile = Join-Path $root 'Data/Regions/bialystok-industrial-c/sbs_cameras.json'
$references = (Get-Content (Join-Path $root 'Data/Regions/bialystok-industrial-c/sbs_references.json') -Raw | ConvertFrom-Json).references
$want = $Cameras -split ','
$renderDir = Join-Path $root "artifacts\g3b-r2\$Name\renders\$Tier-$Lighting$Sub"
New-Item -ItemType Directory -Force $renderDir | Out-Null
& pwsh -NoProfile -File $slot -Acquire -Owner claude-g3b-r2 -PollSeconds 20
try {
    Push-Location $root
    foreach ($group in ($references | Where-Object { $want -contains $_.camera } | Group-Object { "$($_.width)x$($_.height)" })) {
        $first = $group.Group[0]
        $height = [int](1280 * $first.height / $first.width)
        $ids = ($group.Group.camera -join ',')
        $a = @{ Scene = 'WorldC'; Tier = $Tier; Lighting = $Lighting; Width = 1280; Height = $height; Gate3 = $cameraFile; Cameras = $ids; OutputDir = $renderDir }
        if ($Extra -contains '-NoGlass') { $a.NoGlass = $true }
        & (Join-Path $root 'scripts/visual-qa.ps1') @a
    }
} finally {
    & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -NoProfile -File $slot -Release -Owner claude-g3b-r2
    Pop-Location
}
"cams done -> $renderDir"
