$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$main='C:\Users\matma\Documents\Claude\kamion'
if($root -ne (Join-Path $main '.claude/worktrees/gpt-sbs')){throw 'Unexpected worktree'}
Push-Location $root
try {
    if((& git branch --show-current).Trim() -ne 'gpt-sbs-r4'){throw 'Expected r4 branch'}
    $art=$PSScriptRoot
    function Read-Receipt($name){Get-Content -LiteralPath (Join-Path $art $name) -Raw | ConvertFrom-Json}
    function Assert-Hash($path,$hash){if(!$hash -or (Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant() -ne $hash){throw "Changed evidence: $path"}}
    foreach($name in @('REPORT.md','validation-summary.json','generated-restoration.json')){
        if(!(Test-Path -LiteralPath (Join-Path $art $name) -PathType Leaf)){throw "Missing closure: $name"}
    }
    $validation=Read-Receipt 'validation-summary.json'
    if($validation.status -ne 'VERIFIED' -or $validation.gis_failed -ne 0 -or !$validation.heavy_released){throw 'Final validation not complete'}
    foreach($name in @('composition-completed.json','audit-completed.json','fidelity-completed.json','finalgis-completed.json','report-completed.json')){
        $receipt=Read-Receipt $name
        if($receipt.exit_code -ne 0 -or $receipt.source_head -notmatch '^[a-f0-9]{40}$'){throw "Invalid completion: $name"}
        $changed=@(& git diff --name-only $receipt.source_head HEAD -- tools scripts Data game tests art-source)
        if($LASTEXITCODE -ne 0 -or $changed.Count){throw "Production changed since $name"}
    }
    if(Test-Path -LiteralPath (Join-Path $main 'artifacts/locks/heavy-slots/gpt-sbs-r4.slot')){throw 'Own heavy lease still held'}
    if(Test-Path -LiteralPath (Join-Path $main 'artifacts/locks/heavy-slots/queue/gpt-sbs-r4.wait')){throw 'Own heavy task still queued'}
    $dirty=@(& git diff HEAD --name-only -- tools scripts Data game tests art-source)
    if($LASTEXITCODE -ne 0 -or $dirty.Count){throw 'Production/generated files are not restored'}
    $audit=Read-Receipt 'AUDIT.json';$sheets=Read-Receipt 'SHEET-AUDIT.json'
    if($audit.status -ne 'VERIFIED' -or $sheets.status -ne 'VERIFIED' -or $audit.raw_count -ne 168 -or $audit.sheet_count -ne 268 -or $audit.verified_glb_files.Count -ne 128){throw 'Incomplete baseline audit'}
    if($audit.baseline_d51.gate_result -ne 'FAIL'){throw 'Unexpected baseline verdict; recheck report'}
    foreach($row in @($audit.raw_files)+@($audit.sheet_files)){Assert-Hash (Join-Path $root $row.path) $row.sha256}
    $bindings=@{cameras_sha256='sbs_cameras.json';references_sha256='sbs_references.json';world_manifest_sha256='world_manifest.json';materials_spec_sha256='materials_spec.json'}
    foreach($key in $bindings.Keys){Assert-Hash (Join-Path $art ('evidence/inputs/'+$bindings[$key])) $audit.source_hashes.$key}
    Assert-Hash (Join-Path $root 'Data/Regions/bialystok-industrial-c/sbs_recognition.json') $audit.registry_sha256
    $report=Read-Receipt 'report-completed.json'
    Assert-Hash (Join-Path $root 'artifacts/sbs-gate3/latest/index.html') $report.index_sha256
    Assert-Hash (Join-Path $root 'artifacts/sbs-gate3/latest/data.json') $report.data_sha256
    $logs=Join-Path $root 'artifacts/sbs-delivery-logs'
    New-Item -ItemType Directory -Force $logs | Out-Null
    $copies=@(@{source=$art;target=(Join-Path $main 'artifacts/sbs-r4');label='r4'},
        @{source=(Join-Path $root 'artifacts/sbs-gate3/latest');target=(Join-Path $main 'artifacts/sbs-gate3/latest');label='latest'})
    $verified=@()
    foreach($copy in $copies){
        & robocopy $copy.source $copy.target /E /R:1 /W:1 /NFL /NDL /NP "/LOG:$(Join-Path $logs ($copy.label+'-final.log'))" | Out-Null
        $code=$LASTEXITCODE
        if($code -ge 8){throw "Robocopy failed: $($copy.label) $code"}
        $files=@(Get-ChildItem -LiteralPath $copy.source -File -Recurse)
        $hashed=0;$png=0
        foreach($file in $files){
            $relative=[IO.Path]::GetRelativePath($copy.source,$file.FullName)
            $target=Join-Path $copy.target $relative
            if(!(Test-Path -LiteralPath $target -PathType Leaf) -or (Get-Item -LiteralPath $target).Length -ne $file.Length){throw "Missing/different size: $relative"}
            if($file.Extension -in @('.png','.json','.md','.zip','.ps1','.py','.html','.csv','.xml','.log')){
                Assert-Hash $target (Get-FileHash -LiteralPath $file.FullName).Hash.ToLowerInvariant()
                $hashed++;if($file.Extension -eq '.png'){$png++}
            }
        }
        $verified += [ordered]@{label=$copy.label;robocopy_exit_code=$code;files_length_verified=$files.Count;sha_verified=$hashed;png_sha_verified=$png}
    }
    $delivery=[ordered]@{stage='FINAL_ROUND_DELIVERY';delivered_at=(Get-Date -Format o);source_head=(& git rev-parse HEAD).Trim();copies=$verified;note='Artifact copy only. No main commit, merge or push. Existing destination extras preserved.'}
    $path=Join-Path $art 'delivery-receipt.json'
    $delivery | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $path -Encoding utf8
    $target=Join-Path $main 'artifacts/sbs-r4/delivery-receipt.json'
    Copy-Item -LiteralPath $path -Destination $target -Force
    Assert-Hash $target (Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant()
    $delivery | ConvertTo-Json -Depth 8
} finally {Pop-Location}
