# ADR 0141: rebuild WorldEdge (apron, closures, far-field + skyline) in both tier scenes, EditMode tests, then the After renders -
# all under ONE Unity slot. Logs: artifacts/edge-r6c/{rebuild-<Name>.log,editmode-<Name>.log}
param([string]$Name = 'after', [switch]$SkipTests, [switch]$SkipRender)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
. (Join-Path $root 'scripts/env.ps1')
& pwsh -NoProfile -File $slot -Acquire -Owner claude-edge-r6c
$code = 0
try {
    Push-Location $root
    $log = Join-Path $PSScriptRoot "rebuild-$Name.log"
    $code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod', 'Game.World.Import.WorldEdgeBuilder.RebuildEdgeBatch', '-region', 'bialystok-industrial-c')
    if ($code -ne 0 -or -not (Select-String -LiteralPath $log -SimpleMatch -Pattern 'REBUILD_EDGE_RESULT: OK' -Quiet)) { throw "edge rebuild failed ($code), see $log" }
    if (-not $SkipTests) {
        & pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode *> (Join-Path $PSScriptRoot "editmode-$Name.log")
        "editmode exit=$LASTEXITCODE"
    }
} finally {
    & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -NoProfile -File $slot -Release -Owner claude-edge-r6c
    Pop-Location
}
if (-not $SkipRender) { & pwsh -NoProfile -File (Join-Path $PSScriptRoot 'run-vqa.ps1') -Name $Name; $code = $LASTEXITCODE }
"after $Name exit=$code"
exit $code
