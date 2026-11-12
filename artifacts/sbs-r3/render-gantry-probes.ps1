$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Push-Location $taskRoot
try {
    $slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
    $root='artifacts/sbs-r3/gantry-probes'
    $cameraFile=Join-Path $root 'cameras.json'
    $plan=Get-Content (Join-Path $root 'plan.json') -Raw | ConvertFrom-Json
    $import=Get-Content artifacts/sbs-r3/import-completed.json -Raw | ConvertFrom-Json
    $world='Data/Regions/bialystok-industrial-c/generated/world_manifest.json'
    if($import.exit_code -ne 0 -or $import.world_manifest_sha256 -ne (Get-FileHash $world).Hash.ToLowerInvariant()){throw 'Need completed matching import'}
    $paths=[ordered]@{probe_cameras=$cameraFile;production_cameras='Data/Regions/bialystok-industrial-c/sbs_cameras.json';references='Data/Regions/bialystok-industrial-c/sbs_references.json';world_manifest=$world;materials_spec='art-source/world/materials/materials_spec.json'}
    $inputDir=Join-Path $root 'inputs';New-Item -ItemType Directory -Force $inputDir | Out-Null
    foreach($entry in $paths.GetEnumerator()){Copy-Item -LiteralPath $entry.Value -Destination (Join-Path $inputDir ($entry.Key+'.json')) -Force}
    $groups=$plan.probes | Group-Object height
    foreach($group in $groups) {
        $height=[int]$group.Name;$width=1280;$ids=@($group.Group.probe)
        $out=Join-Path $root "renders/$width`x$height"
        pwsh -NoProfile -File $slot -Acquire -Owner gpt-sbs -PollSeconds 1 -StaleHours 87600
        if($LASTEXITCODE -ne 0){throw 'Unity lease failed'}
        try {
            New-Item -ItemType Directory -Force $out | Out-Null
            $capture=[ordered]@{git_sha=(& git rev-parse HEAD).Trim();captured_at_utc=[DateTime]::UtcNow.ToString('o');tier='Low';lighting='overcast';width=$width;height=$height;diagnostic_only=$true;pose_confidence='C';cameras=$ids;status='RUNNING';input_sha256=[ordered]@{}}
            foreach($entry in $paths.GetEnumerator()){$capture.input_sha256[$entry.Key]=(Get-FileHash $entry.Value).Hash.ToLowerInvariant();if($capture.input_sha256[$entry.Key] -ne (Get-FileHash (Join-Path $inputDir ($entry.Key+'.json'))).Hash.ToLowerInvariant()){throw 'Input snapshot mismatch'}}
            $capture | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $out 'capture.json') -Encoding utf8
            pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Width $width -Height $height -Gate3 $cameraFile -Cameras ($ids -join ',') -OutputDir $out
            if($LASTEXITCODE -ne 0){throw 'Diagnostic Unity render failed'}
            foreach($entry in $paths.GetEnumerator()){if($capture.input_sha256[$entry.Key] -ne (Get-FileHash $entry.Value).Hash.ToLowerInvariant()){throw 'Input changed during capture'}}
            if($capture.git_sha -ne (& git rev-parse HEAD).Trim()){throw 'HEAD changed during capture'}
            $capture.render_sha256=[ordered]@{}
            foreach($id in $ids){$capture.render_sha256[$id]=(Get-FileHash (Join-Path $out ($id+'.png'))).Hash.ToLowerInvariant()}
            $capture.status='OK';$capture | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $out 'capture.json') -Encoding utf8
        } finally {
            git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
            pwsh -NoProfile -File $slot -Release -Owner gpt-sbs
        }
    }
} finally {Pop-Location}
