param()
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$expected='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-sbs'
if($root.TrimEnd('\') -ne $expected){throw 'Unexpected source worktree'}
Push-Location $root
try {
    if((& git branch --show-current).Trim() -ne 'gpt-sbs-r3'){throw 'Expected r3 branch'}
    $art=Join-Path $root 'artifacts/sbs-r3'
    $gis=Get-Content (Join-Path $art 'gis-completed.json') -Raw | ConvertFrom-Json
    if($gis.exit_code -ne 0 -or $gis.failed -ne 0 -or !$gis.heavy_released){throw 'GIS not verified complete'}
    foreach($name in @('REPORT.md','AUDIT.json','audit-completed.json','SHEET-AUDIT.json','fidelity-completed.json')) {
        if(!(Test-Path -LiteralPath (Join-Path $art $name) -PathType Leaf)){throw "Missing closure file $name"}
    }
    $fidelity=Get-Content (Join-Path $art 'fidelity-completed.json') -Raw | ConvertFrom-Json
    $sheets=Get-Content (Join-Path $art 'SHEET-AUDIT.json') -Raw | ConvertFrom-Json
    $audit=Get-Content (Join-Path $art 'AUDIT.json') -Raw | ConvertFrom-Json
    $auditReceipt=Get-Content (Join-Path $art 'audit-completed.json') -Raw | ConvertFrom-Json
    if($fidelity.exit_code -ne 0 -or !$fidelity.heavy_released -or $sheets.status -ne 'VERIFIED' -or $sheets.sheet_count -ne 268){throw 'Fidelity or sheet audit incomplete'}
    if($auditReceipt.audit_exit_code -ne 0 -or $auditReceipt.render_head -ne $audit.render_git_sha -or $auditReceipt.counter_rows -ne 168){throw 'Main audit receipt mismatch'}
    foreach($receipt in @($gis,$fidelity)) {
        if($receipt.source_head -notmatch '^[a-f0-9]{40}$'){throw 'Missing validation source commit'}
        $changed=@(& git diff --name-only $receipt.source_head HEAD -- tools scripts Data game tests art-source)
        if($LASTEXITCODE -ne 0 -or $changed.Count){throw 'Production commits changed since validation; only later docs/artifacts allowed'}
    }
    $dirty=@(& git diff HEAD --name-only -- tools scripts Data game tests art-source)
    if($LASTEXITCODE -ne 0 -or $dirty.Count){throw 'Tracked production or generated files differ from HEAD, including staging'}
    $bindings=@{cameras_sha256='sbs_cameras.json';references_sha256='sbs_references.json';world_manifest_sha256='world_manifest.json';materials_spec_sha256='materials_spec.json'}
    foreach($key in $bindings.Keys) {
        $hash=(Get-FileHash -LiteralPath (Join-Path $art ('evidence/inputs/'+$bindings[$key]))).Hash.ToLower()
        if($audit.source_hashes.$key -ne $hash){throw "Audited input changed: $key"}
    }
    foreach($entry in $sheets.files) {
        if((Get-FileHash -LiteralPath (Join-Path $root $entry.path)).Hash.ToLower() -ne $entry.sha256){throw "Audited sheet changed: $($entry.path)"}
    }
    foreach($binding in @(@{path='fidelity/fidelity_summary.json';sha=$fidelity.summary_sha256},@{path='fidelity/fidelity_qa.json';sha=$fidelity.qa_sha256},@{path='recognition-r3-baseline.json';sha=$audit.current_review.sha256})) {
        if((Get-FileHash -LiteralPath (Join-Path $art $binding.path)).Hash.ToLower() -ne $binding.sha){throw "Validated artifact changed: $($binding.path)"}
    }
    if((Get-FileHash -LiteralPath (Join-Path $root 'Data/Regions/bialystok-industrial-c/sbs_recognition.json')).Hash.ToLower() -ne $sheets.current_registry_sha256){throw 'Recognition registry changed since audit'}
    $main='C:\Users\matma\Documents\Claude\kamion'
    $logs=Join-Path $root 'artifacts/sbs-delivery-logs'
    New-Item -ItemType Directory -Force $logs | Out-Null
    $copies=@(@{source=$art;target=(Join-Path $main 'artifacts/sbs-r3');label='r3'},
              @{source=(Join-Path $root 'artifacts/sbs-gate3/latest');target=(Join-Path $main 'artifacts/sbs-gate3/latest');label='latest'})
    $receipts=@()
    foreach($copy in $copies) {
        & robocopy $copy.source $copy.target /E /R:1 /W:1 /NFL /NDL /NP "/LOG:$(Join-Path $logs ($copy.label+'-final.log'))" | Out-Null
        $code=$LASTEXITCODE
        if($code -ge 8){throw "Robocopy failed: $($copy.label) $code"}
        $files=@(Get-ChildItem -LiteralPath $copy.source -File -Recurse)
        $png=0;$critical=0
        foreach($file in $files) {
            $relative=[IO.Path]::GetRelativePath($copy.source,$file.FullName)
            $target=Join-Path $copy.target $relative
            if(!(Test-Path -LiteralPath $target -PathType Leaf) -or (Get-Item -LiteralPath $target).Length -ne $file.Length){throw "Missing or different length: $relative"}
            if($file.Extension -eq '.png' -or $file.Name -in @('REPORT.md','STATUS.md','AUDIT.json','SHEET-AUDIT.json','gis-completed.json','fidelity-completed.json','index.html','data.json','inputs.zip','audit.json')) {
                if((Get-FileHash -LiteralPath $file.FullName).Hash -ne (Get-FileHash -LiteralPath $target).Hash){throw "Copied SHA differs: $relative"}
                if($file.Extension -eq '.png'){$png++}else{$critical++}
            }
        }
        $receipts += [ordered]@{label=$copy.label;robocopy_exit_code=$code;files_length_verified=$files.Count;png_sha_verified=$png;critical_sha_verified=$critical}
    }
    $receipt=[ordered]@{stage='FINAL_ROUND_DELIVERY';delivered_at=(Get-Date -Format o);source_head=(& git rev-parse HEAD).Trim();gis_source_head=$gis.source_head;copies=$receipts;note='No main commit, merge or push; only authorized artifact copy. Extra existing destination files were not removed.'}
    $path=Join-Path $art 'delivery-receipt.json'
    $receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $path -Encoding utf8
    Copy-Item -LiteralPath $path -Destination (Join-Path $main 'artifacts/sbs-r3/delivery-receipt.json') -Force
    $receipt | ConvertTo-Json -Depth 8
} finally {Pop-Location}
