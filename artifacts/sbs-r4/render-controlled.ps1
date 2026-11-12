$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Push-Location $taskRoot
try {
    $slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
    $root='artifacts/sbs-r4/controlled-poses'
    $cameraFile=Join-Path $root 'cameras.json'
    $planFile=Join-Path $root 'plan.json'
    $importFile='artifacts/sbs-r4/import-completed.json'
    $plan=Get-Content $planFile -Raw | ConvertFrom-Json
    $import=Get-Content $importFile -Raw | ConvertFrom-Json
    $loadedPlanHash=(Get-FileHash $planFile).Hash.ToLowerInvariant()
    $loadedImportHash=(Get-FileHash $importFile).Hash.ToLowerInvariant()
    $world='Data/Regions/bialystok-industrial-c/generated/world_manifest.json'
    if($import.exit_code -ne 0 -or $import.world_manifest_sha256 -ne (Get-FileHash $world).Hash.ToLowerInvariant()){throw 'Need completed matching import'}
    if($import.materials_spec_sha256 -ne (Get-FileHash art-source/world/materials/materials_spec.json).Hash.ToLowerInvariant()){throw 'Imported material snapshot changed'}
    function Assert-ProbeInputs {
        if($plan.road_graph_sha256 -ne (Get-FileHash Data/Regions/bialystok-industrial-c/roads.graph.json).Hash.ToLowerInvariant()){throw 'Road graph changed since preparation'}
        if((Get-FileHash $planFile).Hash.ToLowerInvariant() -ne $loadedPlanHash -or (Get-FileHash $importFile).Hash.ToLowerInvariant() -ne $loadedImportHash){throw 'Plan/import receipt changed after loading'}
        $worldHash=(Get-FileHash $world).Hash.ToLowerInvariant()
        $materialHash=(Get-FileHash art-source/world/materials/materials_spec.json).Hash.ToLowerInvariant()
        if($worldHash -ne $import.world_manifest_sha256 -or $materialHash -ne $import.materials_spec_sha256){throw 'Current inputs differ from imported scene'}
        if($plan.world_manifest_sha256 -ne $worldHash -or $plan.probe_cameras_sha256 -ne (Get-FileHash $cameraFile).Hash.ToLowerInvariant()){throw 'Probe plan does not match world/cameras'}
        $checkedSources=@()
        foreach($entry in $plan.production_source_sha256.PSObject.Properties){
            $normalizedName=$entry.Name.Replace('\','/')
            if($normalizedName -notin @('Data/Regions/bialystok-industrial-c/sbs_cameras.json','Data/Regions/bialystok-industrial-c/sbs_references.json')){throw 'Unexpected production source in probe plan'}
            if($normalizedName -in $checkedSources){throw 'Duplicate production source binding'}
            $checkedSources+=$normalizedName
            if((Get-FileHash $entry.Name).Hash.ToLowerInvariant() -ne $entry.Value){throw 'Production source changed since probe preparation'}
        }
        if($checkedSources.Count -ne 2){throw 'Incomplete production source binding'}
        foreach($photo in ($plan.probes | Select-Object photo,photo_sha256 -Unique)){
            $photoPath=[IO.Path]::GetFullPath($photo.photo,$taskRoot)
            if(!$photoPath.StartsWith($taskRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Photo outside task root'}
            if((Get-FileHash $photoPath).Hash.ToLowerInvariant() -ne $photo.photo_sha256){throw 'Comparison photo changed since preparation'}
        }
    }
    Assert-ProbeInputs
    $paths=[ordered]@{road_graph='Data/Regions/bialystok-industrial-c/roads.graph.json';probe_cameras=$cameraFile;probe_plan=$planFile;import_receipt=$importFile;production_cameras='Data/Regions/bialystok-industrial-c/sbs_cameras.json';references='Data/Regions/bialystok-industrial-c/sbs_references.json';world_manifest=$world;materials_spec='art-source/world/materials/materials_spec.json'}
    $inputDir=Join-Path $root 'inputs';New-Item -ItemType Directory -Force $inputDir | Out-Null
    foreach($entry in $paths.GetEnumerator()){Copy-Item -LiteralPath $entry.Value -Destination (Join-Path $inputDir ($entry.Key+'.json')) -Force}
    $groups=$plan.probes | Group-Object height
    $captureHead=(& git rev-parse HEAD).Trim()
    foreach($group in $groups) {
        $height=[int]$group.Name;$width=1280;$ids=@($group.Group.probe)
        $out=Join-Path $root "renders/$width`x$height"
        pwsh -NoProfile -File $slot -Acquire -Owner gpt-sbs -PollSeconds 5 -StaleHours 87600
        if($LASTEXITCODE -ne 0){throw 'Unity lease failed'}
        try {
            Assert-ProbeInputs
            if($captureHead -ne (& git rev-parse HEAD).Trim()){throw 'HEAD changed between diagnostic groups'}
            New-Item -ItemType Directory -Force $out | Out-Null
            $capture=[ordered]@{git_sha=(& git rev-parse HEAD).Trim();captured_at_utc=[DateTime]::UtcNow.ToString('o');tier='Low';lighting='overcast';width=$width;height=$height;diagnostic_only=$true;pose_confidence='C';cameras=$ids;status='RUNNING';input_sha256=[ordered]@{}}
            foreach($entry in $paths.GetEnumerator()){$capture.input_sha256[$entry.Key]=(Get-FileHash $entry.Value).Hash.ToLowerInvariant();if($capture.input_sha256[$entry.Key] -ne (Get-FileHash (Join-Path $inputDir ($entry.Key+'.json'))).Hash.ToLowerInvariant()){throw 'Input snapshot mismatch'}}
            $capture | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $out 'capture.json') -Encoding utf8
            pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Width $width -Height $height -Gate3 $cameraFile -Cameras ($ids -join ',') -OutputDir $out
            if($LASTEXITCODE -ne 0){throw 'Diagnostic Unity render failed'}
            Assert-ProbeInputs
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



