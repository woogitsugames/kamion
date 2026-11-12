$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Push-Location $root
try {
    $owner=(& git branch --show-current).Trim()
    if($owner -ne 'gpt-sbs-r4'){throw 'Expected r4'}
    $preparation=Get-Content artifacts/sbs-r4/preparation-completed.json -Raw | ConvertFrom-Json
    if($preparation.lfs_checkout_exit_code -ne 0 -or $preparation.merged_main -notmatch '^[a-f0-9]{40}$'){throw 'Preparation incomplete'}
    $slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
    $env:PYTHONUNBUFFERED='1'
    foreach($step in @('Materials','World')) {
        pwsh -NoProfile -File $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 5 -StaleHours 87600
        if($LASTEXITCODE -ne 0){throw "No heavy lease for $step"}
        try {
            $sourceHead=(& git rev-parse HEAD).Trim()
            $started=[DateTime]::UtcNow
            if($step -eq 'Materials') {
                uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py *> artifacts/sbs-r4/build-materials.log
                if($LASTEXITCODE -ne 0){throw 'Material generator failed'}
                $record=[ordered]@{source_head=$sourceHead;started_at_utc=$started.ToString('o');completed_at_utc=[DateTime]::UtcNow.ToString('o');exit_code=0;materials_spec_sha256=(Get-FileHash art-source/world/materials/materials_spec.json).Hash.ToLower()}
                $record | ConvertTo-Json | Set-Content artifacts/sbs-r4/materials-completed.json -Encoding utf8
            } else {
                uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> artifacts/sbs-r4/build-world.log
                if($LASTEXITCODE -ne 0){throw 'World generator failed'}
                if(Select-String -LiteralPath artifacts/sbs-r4/build-world.log -SimpleMatch 'fallback=True' -Quiet){throw 'World used fallback'}
                $record=[ordered]@{source_head=$sourceHead;started_at_utc=$started.ToString('o');completed_at_utc=[DateTime]::UtcNow.ToString('o');exit_code=0;world_manifest_sha256=(Get-FileHash Data/Regions/bialystok-industrial-c/generated/world_manifest.json).Hash.ToLower();materials_spec_sha256=(Get-FileHash art-source/world/materials/materials_spec.json).Hash.ToLower();fallback_true=$false}
                $record | ConvertTo-Json | Set-Content artifacts/sbs-r4/world-completed.json -Encoding utf8
            }
        } finally {pwsh -NoProfile -File $slot -Release -Pool heavy -Owner $owner}
        Add-Content artifacts/sbs-r4/STATUS.md -Encoding utf8 -Value "`n$(Get-Date -Format o): generator $step zakończony exit0; osobny heavy zwolniony. Szczegóły i SHA w receipcie kroku."
        Write-Host "Completed $step; lease released before next step."
    }
    $materials=Get-Content artifacts/sbs-r4/materials-completed.json -Raw | ConvertFrom-Json
    $world=Get-Content artifacts/sbs-r4/world-completed.json -Raw | ConvertFrom-Json
    if($materials.materials_spec_sha256 -ne $world.materials_spec_sha256){throw 'Material spec changed between steps'}
    [ordered]@{source_head=$world.source_head;materials_source_head=$materials.source_head;merged_main=$preparation.merged_main;started_at_utc=$materials.started_at_utc;completed_at_utc=$world.completed_at_utc;materials_exit=0;world_exit=0;world_manifest_sha256=$world.world_manifest_sha256;materials_spec_sha256=$world.materials_spec_sha256;fallback_true=$false;heavy_released_between_steps=$true;queue='FIFO, no Priority'} | ConvertTo-Json -Depth 5 | Set-Content artifacts/sbs-r4/baseline-completed.json -Encoding utf8
} finally {Pop-Location}
