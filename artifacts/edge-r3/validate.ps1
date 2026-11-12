param([ValidateSet('Before','After','Tests')][string]$Phase, [switch]$SkipRebuild)
$ErrorActionPreference = 'Stop'
$edgeRoot = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $edgeRoot
. scripts/env.ps1
$out = $PSScriptRoot
$statusRelative = 'artifacts/' + (Split-Path $out -Leaf) + '/STATUS.md'
$slotScript = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
function Save-Step([string]$message) {
    Add-Content "$out/STATUS.md" "$(Get-Date -Format o) $message"
    git add -f $statusRelative
    git commit -m "wip(edge): $message"
    if ($LASTEXITCODE -ne 0) { throw 'WIP checkpoint failed' }
}
function With-UnitySlot([scriptblock]$action) {
    & pwsh $slotScript -Acquire -Owner gpt-edge -Pool unity -PollSeconds 7 -StaleHours 100000
    if ($LASTEXITCODE -ne 0) { throw 'Slot acquisition failed' }
    try { & $action }
    finally {
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
        & pwsh $slotScript -Release -Owner gpt-edge -Pool unity -StaleHours 100000
    }
}
if ($Phase -eq 'Before') {
    # The imported main scene is the baseline; only the edge is rebuilt after this phase.
    # It is deliberately not reimported with the edited WorldEdgeBuilder before baseline capture.
    $label = 'before'
} elseif ($Phase -eq 'After') {
    if (Test-Path -LiteralPath "$out/After.complete") { Remove-Item -LiteralPath "$out/After.complete" }
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
            $captureInputs = @('Data/Regions/bialystok-industrial-c/sbs_references.json',
                'Data/Regions/bialystok-industrial-c/generated/world_manifest.json',
                'art-source/world/materials/materials_spec.json',
                "game/Assets/_Generated/World/bialystok-industrial-c/$scene.unity",
                'game/Assets/_Generated/World/bialystok-industrial-c/Meshes/world_edge.asset',
                "game/Assets/_Generated/World/bialystok-industrial-c/Meshes/$tier/world_edge_far.asset")
            $hashes = @{}
            foreach ($inputFile in $captureInputs) { $hashes[$inputFile] = (Get-FileHash -LiteralPath $inputFile -Algorithm SHA256).Hash }
            $hashes['proof-cameras.json'] = (Get-FileHash -LiteralPath "$out/proof-cameras.json" -Algorithm SHA256).Hash
            $capture = @{branch=(git branch --show-current);commit=(git rev-parse HEAD);phase=$label;tier=$tier;lighting=$lighting;inputs_sha256=$hashes;started=(Get-Date -Format o)}
            & pwsh scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $lighting `
                -Gate3 "$out/proof-cameras.json" -OutputDir "$out/$label/$tier-$lighting"
            if ($LASTEXITCODE -ne 0) { throw "Render failed: $label/$tier-$lighting" }
            $proofIds = @((Get-Content "$out/proof-cameras.json" -Raw | ConvertFrom-Json).cameras | ForEach-Object id)
            $statIds = @(Select-String -LiteralPath "$out/$label/$tier-$lighting/stats.txt" -Pattern '^(.+): objects=' | ForEach-Object { $_.Matches[0].Groups[1].Value })
            foreach ($cameraId in $proofIds + $statIds | Sort-Object -Unique) {
                $frame = "$out/$label/$tier-$lighting/$cameraId.png"
                if (-not (Test-Path -LiteralPath $frame) -or (Get-Item -LiteralPath $frame).Length -eq 0) {
                    throw "Missing camera frame: $cameraId"
                }
                if ($cameraId -notin $statIds) { throw "Missing camera statistics: $cameraId" }
            }
            foreach ($inputFile in $captureInputs) {
                if ((Get-FileHash -LiteralPath $inputFile -Algorithm SHA256).Hash -ne $hashes[$inputFile]) { throw "Input changed during capture: $inputFile" }
            }
            if ((Get-FileHash -LiteralPath "$out/proof-cameras.json" -Algorithm SHA256).Hash -ne $hashes['proof-cameras.json']) { throw 'Camera file changed during capture' }
            $capture['finished'] = Get-Date -Format o
            $capture['expected_proof_cameras'] = $proofIds.Count
            $capture['captured_camera_statistics'] = $statIds.Count
            $capture | ConvertTo-Json -Depth 6 | Set-Content "$out/$label/$tier-$lighting/capture-inputs.json"
        }
        Save-Step "Zapisano rendery $label/$tier-$lighting wszystkich kamer; ocena PNG i budżetu nadal w toku."
    }
}
"$(Get-Date -Format o)" | Set-Content "$out/$Phase.complete"
