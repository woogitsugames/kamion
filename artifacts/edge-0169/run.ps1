# ADR 0169: rebuild WorldEdge in place, optional EditMode, render the edge cameras (Low clear + overcast)
# -> artifacts/edge-0169/<Name>/Low-<lighting>. ONE Unity slot. Logs: *-<Name>.log
param([string]$Name = 'after', [switch]$Tests, [switch]$SkipRebuild)
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
. (Join-Path $root 'scripts/env.ps1')
& pwsh -NoProfile -File $slot -Acquire -Owner claude-edge-0169
try {
    Push-Location $root
    $ok = $true
    if (-not $SkipRebuild) {
        $log = Join-Path $PSScriptRoot "rebuild-$Name.log"
        $code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod', 'Game.World.Import.WorldEdgeBuilder.RebuildEdgeBatch', '-region', 'bialystok-industrial-c')
        $ok = ($code -eq 0) -and (Select-String -LiteralPath $log -SimpleMatch -Pattern 'REBUILD_EDGE_RESULT: OK' -Quiet)
        "rebuild exit=$code ok=$ok"
    }
    if ($ok) {
        if ($Tests) {
            & pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode *> (Join-Path $PSScriptRoot "editmode-$Name.log")
            "editmode exit=$LASTEXITCODE"
        }
        foreach ($l in 'clear', 'overcast') {
            $dir = Join-Path $PSScriptRoot "$Name\Low-$l"
            New-Item -ItemType Directory -Force $dir | Out-Null
            & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting $l -Cameras 'edge-east,edge-west,edge-north,edge-south' -OutputDir $dir *> (Join-Path $PSScriptRoot "vqa-$Name-$l.log")
            "vqa $l exit=$LASTEXITCODE"
        }
    }
} finally {
    & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -NoProfile -File $slot -Release -Owner claude-edge-0169
    Pop-Location
}
"$Name done"
