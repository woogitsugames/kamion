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
    foreach($name in @('REPORT.md','AUDIT.json','SHEET-AUDIT.json','fidelity-completed.json')) {
        if(!(Test-Path -LiteralPath (Join-Path $art $name) -PathType Leaf)){throw "Missing closure file $name"}
    }
    $fidelity=Get-Content (Join-Path $art 'fidelity-completed.json') -Raw | ConvertFrom-Json
    $sheets=Get-Content (Join-Path $art 'SHEET-AUDIT.json') -Raw | ConvertFrom-Json
    if($fidelity.exit_code -ne 0 -or !$fidelity.heavy_released -or $sheets.status -ne 'VERIFIED' -or $sheets.sheet_count -ne 268){throw 'Fidelity or sheet audit incomplete'}
    $generated=@(& git diff --name-only -- Data/Regions/bialystok-industrial-c/generated Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json art-source/world/props)
    if($generated.Count){throw 'Generated side effects must be restored before delivery'}
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
