# ADR 0141: renders control + gate3 cameras (2340x1080) and the SBS photo-pose cameras (per photo aspect) under ONE Unity slot.
# Output: artifacts/edge-r6c/<Name>/<Tier>-<Lighting>/{*.png,stats*.txt}
param([string]$Name = 'baseline', [string]$Tier = 'Low', [string[]]$Lighting = @('clear', 'overcast'), [switch]$SkipControl, [string]$Rq = '')
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$reg = Join-Path $root 'Data/Regions/bialystok-industrial-c'
$references = (Get-Content (Join-Path $reg 'sbs_references.json') -Raw | ConvertFrom-Json).references
function Get-AspectKey($width, $height) {
    $a = [int]$width; $b = [int]$height
    while ($b -ne 0) { $r = $a % $b; $a = $b; $b = $r }
    return "$([int]($width/$a))x$([int]($height/$a))"
}
& pwsh -NoProfile -File $slot -Acquire -Owner claude-edge-r6c
$code = 0
try {
    Push-Location $root
    foreach ($l in $Lighting) {
        $dir = Join-Path $root "artifacts\edge-r6c\$Name\$Tier-$l"
        New-Item -ItemType Directory -Force $dir | Out-Null
        $extra = @(); if ($Rq) { $extra = @('-Rq', $Rq) }
        if (-not $SkipControl) {
            & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier $Tier -Lighting $l -Gate3 (Join-Path $reg 'gate3_cameras.json') -OutputDir $dir @extra
            if ($LASTEXITCODE -ne 0) { $code = $LASTEXITCODE; break }
            Copy-Item -LiteralPath (Join-Path $dir 'stats.txt') -Destination (Join-Path $dir 'stats-control.txt')
        }
        foreach ($group in ($references | Group-Object { Get-AspectKey $_.width $_.height })) {
            $first = $group.Group[0]
            $height = [int](1280 * $first.height / $first.width)
            & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier $Tier -Lighting $l -Width 1280 -Height $height -Gate3 (Join-Path $reg 'sbs_cameras.json') -Cameras ($group.Group.camera -join ',') -OutputDir $dir @extra
            if ($LASTEXITCODE -ne 0) { $code = $LASTEXITCODE; break }
            Copy-Item -LiteralPath (Join-Path $dir 'stats.txt') -Destination (Join-Path $dir "stats-$($group.Name).txt")
        }
        if ($code -ne 0) { break }
    }
} finally {
    & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -NoProfile -File $slot -Release -Owner claude-edge-r6c
    Pop-Location
}
"vqa $Name exit=$code"
exit $code
