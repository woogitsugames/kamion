param([switch]$ResumeAfter)
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $root
$out = $PSScriptRoot
. scripts/env.ps1
function Wait-Phone {
    while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') {
        Write-Output "$(Get-Date -Format o) PHONE_RUN active; Unity deferred"
        Start-Sleep -Seconds 60
    }
}
if (!(Test-Path "$out/EVIDENCE_COMPLETE")) { throw 'Finish the primary matrix and tests first' }
$phases = if ($ResumeAfter) { @('after') } else { @('before','after') }
foreach ($phase in $phases) {
    & uv run --project tools/worldgen python "$out/generate_evidence.py" $phase > "$out/skyline-generate-$phase.log"
    if ($LASTEXITCODE -ne 0) { throw 'Generation failed' }
    Wait-Phone
    try {
        $code = Invoke-UnityBatch -LogFile "$out/skyline-rebuild-$phase.log" -Arguments @('-executeMethod','Game.World.Import.WorldEdgeBuilder.RebuildEdgeBatch','-region','bialystok-industrial-c')
        if ($code -ne 0) { throw 'Rebuild failed' }
    } finally { git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings }
    foreach ($tier in @('Low','High')) {
        $scene = if ($tier -eq 'High') { 'WorldC_High' } else { 'WorldC' }
        foreach ($lighting in @('clear','overcast')) {
            Wait-Phone
            try {
                & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $lighting -Cameras edge-pietrasze-skyline -Gate3 "$out/skyline-cameras.json" -OutputDir "$out/skyline/$phase/$tier-$lighting"
                if ($LASTEXITCODE -ne 0) { throw 'Render failed' }
            } finally { git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings }
        }
    }
}
'SKYLINE_COMPLETE' | Set-Content "$out/SKYLINE_COMPLETE"
