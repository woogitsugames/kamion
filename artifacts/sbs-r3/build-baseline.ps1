$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Push-Location $root
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$owner=(& git branch --show-current).Trim()
if($owner -ne 'gpt-sbs-r3'){throw 'Wrong branch for r3 baseline'}
try {
    pwsh -NoProfile -File $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 1 -StaleHours 87600
    if($LASTEXITCODE -ne 0){throw 'No heavy lease'}
    try {
        $env:PYTHONUNBUFFERED='1'
        $sourceHead=(& git rev-parse HEAD).Trim()
        $started=[DateTime]::UtcNow
        uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py *> artifacts/sbs-r3/build-materials.log
        if($LASTEXITCODE -ne 0){throw 'Material generator failed'}
        uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> artifacts/sbs-r3/build-world.log
        if($LASTEXITCODE -ne 0){throw 'World generator failed'}
        if(Select-String -LiteralPath artifacts/sbs-r3/build-world.log -SimpleMatch 'fallback=True' -Quiet){throw 'World used fallback'}
        [ordered]@{source_head=$sourceHead;started_at_utc=$started.ToString('o');completed_at_utc=[DateTime]::UtcNow.ToString('o');materials_exit=0;world_exit=0;world_manifest_sha256=(Get-FileHash Data/Regions/bialystok-industrial-c/generated/world_manifest.json).Hash.ToLowerInvariant();materials_spec_sha256=(Get-FileHash art-source/world/materials/materials_spec.json).Hash.ToLowerInvariant();fallback_true=$false} | ConvertTo-Json -Depth 5 | Set-Content artifacts/sbs-r3/baseline-completed.json -Encoding utf8
    } finally {pwsh -NoProfile -File $slot -Release -Pool heavy -Owner $owner}
} finally {Pop-Location}
