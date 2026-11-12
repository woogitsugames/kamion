# ADR 0141 r6d: rebuild WorldEdge (merged closures, brighter sign paint), EditMode, then renders of the edge cameras and the two
# EC SBS frames (Low clear + overcast) -> artifacts/edge-r6c/r6d/<Tier>-<Lighting>. ONE Unity slot. Logs: *-r6d.log
param([switch]$SkipTests)
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$reg = Join-Path $root 'Data/Regions/bialystok-industrial-c'
. (Join-Path $root 'scripts/env.ps1')
& pwsh -NoProfile -File $slot -Acquire -Owner claude-edge-r6d
try {
    Push-Location $root
    $log = Join-Path $PSScriptRoot 'rebuild-r6d.log'
    $code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod', 'Game.World.Import.WorldEdgeBuilder.RebuildEdgeBatch', '-region', 'bialystok-industrial-c')
    $ok = ($code -eq 0) -and (Select-String -LiteralPath $log -SimpleMatch -Pattern 'REBUILD_EDGE_RESULT: OK' -Quiet)
    "rebuild exit=$code ok=$ok"
    if ($ok) {
        if (-not $SkipTests) {
            & pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode *> (Join-Path $PSScriptRoot 'editmode-r6d.log')
            "editmode exit=$LASTEXITCODE"
        }
        foreach ($l in 'clear', 'overcast') {
            $dir = Join-Path $PSScriptRoot "r6d\Low-$l"
            New-Item -ItemType Directory -Force $dir | Out-Null
            & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting $l -Cameras 'edge-east,edge-west,edge-north,edge-south,dk8-dk19-exit' -OutputDir $dir *> (Join-Path $PSScriptRoot "vqa-r6d-$l-control.log")
            "vqa control $l exit=$LASTEXITCODE"
            & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting $l -Width 1280 -Height 960 -Gate3 (Join-Path $reg 'sbs_cameras.json') -Cameras 'sbs-g3-b-297817221966185' -OutputDir $dir *> (Join-Path $PSScriptRoot "vqa-r6d-$l-297817.log")
            "vqa 297817 $l exit=$LASTEXITCODE"
        }
    }
} finally {
    & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -NoProfile -File $slot -Release -Owner claude-edge-r6d
    Pop-Location
}
"r6d done"
