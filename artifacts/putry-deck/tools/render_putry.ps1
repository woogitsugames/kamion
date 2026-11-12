# ADR 0133: SBS renders of the G3-B frames next to the DK8 / Putry decks (subset of sbs-gate3.ps1, same cameras/sizes).
param([Parameter(Mandatory)][string]$OutDir, [string[]]$Lighting = @('overcast', 'clear'), [string]$Tier = 'Low',
      [string]$Owner = 'claude-putry-deck')
$ErrorActionPreference = 'Stop'
$root = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\putry-deck'
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$cams = Join-Path $root 'Data/Regions/bialystok-industrial-c/sbs_cameras.json'
$groups = @(
    @{ w = 1280; h = 960; ids = 'sbs-g3-b-494288258686575,sbs-g3-b-4312632558767412,sbs-g3-b-468026894483428,sbs-g3-b-339463879238809,sbs-g3-b-209622370971977,sbs-g3-b-326454015490067,sbs-g3-b-810525063224609,sbs-g3-b-810896133189484,sbs-g3-b-1528935774382039' },
    @{ w = 1280; h = 720; ids = 'sbs-g3-b-182011943700132' })
Push-Location $root
try {
    foreach ($light in $Lighting) {
        $dir = Join-Path $OutDir "$Tier-$light"
        New-Item -ItemType Directory -Force $dir | Out-Null
        foreach ($g in $groups) {
            & pwsh -NoProfile -File $slot -Acquire -Owner $Owner
            if ($LASTEXITCODE -ne 0) { throw 'slot' }
            try {
                & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier $Tier -Lighting $light -Width $g.w -Height $g.h -Gate3 $cams -Cameras $g.ids -OutputDir $dir
                if ($LASTEXITCODE -ne 0) { throw "render $light" }
                Copy-Item (Join-Path $dir 'stats.txt') (Join-Path $dir "stats-$($g.w)x$($g.h).txt")
            } finally {
                & git -C $root restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
                $res = Join-Path $root 'game/Assets/Resources'
                if ((Test-Path $res) -and -not (Get-ChildItem $res -Force)) { Remove-Item $res -Force; Remove-Item "$res.meta" -Force -ErrorAction SilentlyContinue }
                & pwsh -NoProfile -File $slot -Release -Owner $Owner
            }
        }
    }
} finally { Pop-Location }
