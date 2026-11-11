param([ValidateSet('Before','After','Tests')][string]$Phase, [switch]$SkipRebuild)
$ErrorActionPreference = 'Stop'
$edgeRoot = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $edgeRoot
. scripts/env.ps1
$out = $PSScriptRoot
function Save-Step([string]$message) {
    Add-Content "$out/STATUS.md" "$(Get-Date -Format o) $message"
    git add -f artifacts/edge-r1/STATUS.md
    git commit -m "wip(edge): $message"
    if ($LASTEXITCODE -ne 0) { throw 'WIP checkpoint failed' }
}
function With-UnitySlot([scriptblock]$action) {
    & pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-edge -PollSeconds 5
    if ($LASTEXITCODE -ne 0) { throw 'Slot acquisition failed' }
    try { & $action }
    finally {
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
        & pwsh scripts/unity-slot.ps1 -Release -Owner gpt-edge
    }
}
if ($Phase -eq 'Before') {
    # The imported main scene is the baseline; only the edge is rebuilt after this phase.
    # It is deliberately not reimported with the edited WorldEdgeBuilder before baseline capture.
    $label = 'before'
} elseif ($Phase -eq 'After') {
    if (-not $SkipRebuild) { With-UnitySlot {
        $code = Invoke-UnityBatch -LogFile "$out/rebuild-after.log" -Arguments @(
            '-executeMethod','Game.World.Import.WorldEdgeBuilder.RebuildEdgeBatch',
            '-region','bialystok-industrial-c')
        if ($code -ne 0) { throw "Edge rebuild failed: $code" }
        if (-not (Select-String -LiteralPath "$out/rebuild-after.log" -SimpleMatch -Pattern 'REBUILD_EDGE_RESULT: OK' -Quiet)) {
            throw 'Missing successful rebuild marker'
        }
    } }
    elseif (-not (Select-String -LiteralPath "$out/rebuild-after.log" -SimpleMatch -Pattern 'REBUILD_EDGE_RESULT: OK' -Quiet)) {
        throw 'Cannot resume rendering without a successful edge rebuild marker'
    }
    Save-Step 'Przebudowano wyłącznie WorldEdge w scenach Low i High; wynik wizualny do sprawdzenia.'
    $label = 'after'
} else {
    With-UnitySlot {
        & pwsh scripts/test.ps1 -Platform EditMode
        if ($LASTEXITCODE -ne 0) { throw 'EditMode failed' }
    }
    Save-Step 'Zakończono testy EditMode; szczegółowy wynik w artifacts/tests.'
    exit 0
}
foreach ($tier in @('Low','High')) {
    foreach ($lighting in @('clear','overcast')) {
        $scene = if ($tier -eq 'High') { 'WorldC_High' } else { 'WorldC' }
        With-UnitySlot {
            & pwsh scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $lighting `
                -Gate3 "$out/proof-cameras.json" -OutputDir "$out/$label/$tier-$lighting"
            if ($LASTEXITCODE -ne 0) { throw "Render failed: $label/$tier-$lighting" }
        }
        Save-Step "Zapisano rendery $label/$tier-$lighting wszystkich kamer; ocena PNG i budżetu nadal w toku."
    }
}
"$(Get-Date -Format o)" | Set-Content "$out/$Phase.complete"
