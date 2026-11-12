# Renders the SBS photo-pose cameras (Low overcast by default) under a Unity slot into artifacts/g3b-r2/<Name>.
# Same render calls as scripts/sbs-gate3.ps1 (one visual-qa run per photo aspect ratio, stats kept per group); the
# sheet composition (heavy slot) is a separate step: run-compose.ps1 -Name <Name>.
param([string]$Name = 'baseline', [string]$Tier = 'Low', [string]$Lighting = 'overcast')
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$cameraFile = Join-Path $root 'Data/Regions/bialystok-industrial-c/sbs_cameras.json'
$references = (Get-Content (Join-Path $root 'Data/Regions/bialystok-industrial-c/sbs_references.json') -Raw | ConvertFrom-Json).references
function Get-AspectKey($width, $height) {
    $a = [int]$width; $b = [int]$height
    while ($b -ne 0) { $r = $a % $b; $a = $b; $b = $r }
    return "$([int]($width/$a))x$([int]($height/$a))"
}
$renderDir = Join-Path $root "artifacts\g3b-r2\$Name\renders\$Tier-$Lighting"
New-Item -ItemType Directory -Force $renderDir | Out-Null
& pwsh -NoProfile -File $slot -Acquire -Owner claude-g3b-r2 -PollSeconds 5
$code = 0
try {
    Push-Location $root
    foreach ($group in ($references | Group-Object { Get-AspectKey $_.width $_.height })) {
        $first = $group.Group[0]
        $width = 1280
        $height = [int]($width * $first.height / $first.width)
        $ids = ($group.Group.camera -join ',')
        & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier $Tier -Lighting $Lighting -Width $width -Height $height -Gate3 $cameraFile -Cameras $ids -OutputDir $renderDir
        if ($LASTEXITCODE -ne 0) { $code = $LASTEXITCODE; break }
        Copy-Item -LiteralPath (Join-Path $renderDir 'stats.txt') -Destination (Join-Path $renderDir "stats-$($group.Name).txt")
    }
} finally {
    & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -NoProfile -File $slot -Release -Owner claude-g3b-r2
    Pop-Location
}
"sbs render exit=$code -> $renderDir"
