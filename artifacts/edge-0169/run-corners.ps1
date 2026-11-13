# ADR 0169: corner cameras (crossing closures). after (current scene) -> rebuild with the importer of main -> before -> rebuild with the branch.
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$files = 'game/Assets/_Project/World/Import/WorldEdgeBuilder.cs', 'game/Assets/_Project/World/Import/RegionImporter.cs', 'game/Assets/_Project/World/Runtime/WorldBoundary.cs',
         'game/Assets/_Project/Tests/EditMode/WorldEdgeClosureSkylineTests.cs'
$newTest = Join-Path $root 'game/Assets/_Project/Tests/EditMode/WorldEdgeClosureDuplicateTests.cs'
. (Join-Path $root 'scripts/env.ps1')
function Render($name) {
    $dir = Join-Path $PSScriptRoot "$name\Low-clear"
    New-Item -ItemType Directory -Force $dir | Out-Null
    & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -Gate3 (Join-Path $PSScriptRoot 'corner_cameras.json') -Cameras 'edge-corner-east-batorego,edge-corner-south-kombatantow' -OutputDir $dir *> (Join-Path $PSScriptRoot "vqa-$name.log")
    "vqa $name exit=$LASTEXITCODE"
}
function Rebuild($name) {
    $log = Join-Path $PSScriptRoot "rebuild-$name.log"
    $code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod', 'Game.World.Import.WorldEdgeBuilder.RebuildEdgeBatch', '-region', 'bialystok-industrial-c')
    "rebuild $name exit=$code ok=$((Select-String -LiteralPath $log -SimpleMatch -Pattern 'REBUILD_EDGE_RESULT: OK' -Quiet))"
}
& pwsh -NoProfile -File $slot -Acquire -Owner claude-edge-0169
try {
    Push-Location $root
    Render 'corners-after'
    & git -C $root checkout 47ee3f123 -- @files   # importer of main
    Move-Item $newTest "$newTest.off"; if (Test-Path "$newTest.meta") { Move-Item "$newTest.meta" "$newTest.meta.off" }
    try { Rebuild 'corners-before'; Render 'corners-before' }
    finally {
        & git -C $root checkout HEAD -- @files
        Move-Item "$newTest.off" $newTest; if (Test-Path "$newTest.meta.off") { Move-Item "$newTest.meta.off" "$newTest.meta" }
    }
    Rebuild 'final'
} finally {
    & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -NoProfile -File $slot -Release -Owner claude-edge-0169
    Pop-Location
}
"corners done"
