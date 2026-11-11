param([switch]$SkipGis, [switch]$ResumeAfter)
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $root
$out = $PSScriptRoot
$phoneLock = 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN'
function Wait-Phone {
    while (Test-Path -LiteralPath $phoneLock) {
        Write-Output "$(Get-Date -Format o) PHONE_RUN active; Unity deferred"
        Start-Sleep -Seconds 60
    }
}
function Restore-UnityEffects {
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
function Render-Matrix([string]$phase) {
    foreach ($tier in @('Low','High')) {
        $scene = if ($tier -eq 'High') { 'WorldC_High' } else { 'WorldC' }
        foreach ($lighting in @('clear','overcast')) {
            Wait-Phone
            try {
                & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $lighting -Cameras 'edge-north,edge-east,edge-south,edge-west,dk8-dk19-exit,edge-pietrasze-horizon,edge-pietrasze-overview' -Gate3 "$out/edge-cameras.json" -OutputDir "$out/$phase/$tier-$lighting"
                if ($LASTEXITCODE -ne 0) { throw "Render failed: $phase/$tier/$lighting" }
            } finally { Restore-UnityEffects }
        }
    }
}
# The world baseline must be generated before this render-only orchestration starts.
if (!(Select-String "$out/build-before.log" -Pattern '\[world.*\] done' -Quiet)) {
    throw 'Run the merged world generation first; build-before.log has no completion marker'
}
# A local texture preparation may run while the phone owns Unity; never import half-written sets.
while ((Test-Path "$out/materials-prepare.log") -and
       !(Select-String "$out/materials-prepare.log" -Pattern 'wrote.*materials_spec.json.*total' -Quiet)) {
    if (Select-String "$out/materials-prepare.log" -Pattern 'Traceback|Error:' -Quiet) {
        throw 'Local material preparation failed; inspect materials-prepare.log'
    }
    Start-Sleep -Seconds 10
}
if (!$ResumeAfter) {
    & uv run --project tools/worldgen python "$out/generate_evidence.py" before > "$out/generate-before.log"
    if ($LASTEXITCODE -ne 0) { throw 'Before generation failed' }
    Wait-Phone
    try {
        & pwsh -NoProfile -File scripts/import-region.ps1 -Region bialystok-industrial-c
        if ($LASTEXITCODE -ne 0) { throw 'Import failed' }
    } finally { Restore-UnityEffects }
    Render-Matrix before
}
& uv run --project tools/worldgen python "$out/generate_evidence.py" after > "$out/generate-after.log"
if ($LASTEXITCODE -ne 0) { throw 'After generation failed' }
if (!$SkipGis) {
    & uv run --project tools/worldgen python -m pytest tests/gis -q > "$out/gis-after.log" 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'GIS validation failed' }
}
Wait-Phone
. scripts/env.ps1
try {
    $code = Invoke-UnityBatch -LogFile "$out/rebuild-after.log" -Arguments @('-executeMethod','Game.World.Import.WorldEdgeBuilder.RebuildEdgeBatch','-region','bialystok-industrial-c')
    if ($code -ne 0) { throw "Edge rebuild failed: $code" }
} finally { Restore-UnityEffects }
Render-Matrix after
foreach ($platform in @('EditMode','PlayMode')) {
    Wait-Phone
    try {
        $args = @('-NoProfile','-File','scripts/test.ps1','-Platform',$platform)
        if ($platform -eq 'PlayMode') { $args += @('-Filter','WorldEdgeRecoveryTests') }
        & pwsh @args
        if ($LASTEXITCODE -ne 0) { throw "$platform failed" }
    } finally { Restore-UnityEffects }
}
'EVIDENCE_COMPLETE' | Set-Content "$out/EVIDENCE_COMPLETE"
