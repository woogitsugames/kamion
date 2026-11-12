# Metadata-only closure. Execute after all actual validation jobs, before restoring generated files.
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Push-Location $root
try {
    if((& git branch --show-current).Trim() -ne 'gpt-sbs-r4'){throw 'Expected r4'}
    $main='C:/Users/matma/Documents/Claude/kamion'
    foreach($suffix in @('heavy-slots/gpt-sbs-r4.slot','heavy-slots/queue/gpt-sbs-r4.wait','unity-slots/gpt-sbs.slot','unity-slots/queue/gpt-sbs.wait')){
        if(Test-Path -LiteralPath (Join-Path $main ('artifacts/locks/'+$suffix))){throw "Own job not finished: $suffix"}
    }
    $bindings=[ordered]@{}
    foreach($name in @('composition-completed.json','audit-completed.json','fidelity-completed.json','finalgis-completed.json','report-completed.json','test-test_sbs_gate3-completed.json','test-test_sbs_evidence_script-completed.json')){
        $path=Join-Path $PSScriptRoot $name
        $receipt=Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
        if($receipt.exit_code -ne 0 -or $receipt.source_head -notmatch '^[a-f0-9]{40}$'){throw "Failed/missing receipt: $name"}
        $changed=@(& git diff --name-only $receipt.source_head HEAD -- tools scripts Data game tests art-source)
        if($LASTEXITCODE -ne 0 -or $changed.Count){throw "Production sources changed since $name"}
        $bindings[$name]=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant()
    }
    $log=Join-Path $PSScriptRoot 'pytest-gis.log'
    $line=(@(Get-Content -LiteralPath $log | Select-String '\d+ passed.* in [\d.]+s') | Select-Object -Last 1).Line
    if(!$line){throw 'Missing final pytest summary'}
    $line=$line.Trim('= '.ToCharArray())
    if($line -notmatch '^(?:\d+ (?:passed|failed|skipped|xfailed|xpassed|errors?)(?:, )?)+ in ([\d.]+)s'){throw 'Unexpected pytest summary format'}
    $seconds=[double]$Matches[1]
    $counts=@{}
    foreach($match in [regex]::Matches($line,'(\d+) (passed|failed|skipped|xfailed|xpassed|errors?)')){$counts[$match.Groups[2].Value]=[int]$match.Groups[1].Value}
    if(!$counts.passed -or $counts.failed -or $counts.error -or $counts.errors){throw 'GIS did not pass'}
    $fidelity=Get-Content (Join-Path $PSScriptRoot 'fidelity/fidelity_summary.json') -Raw | ConvertFrom-Json
    $qa='Data/Regions/bialystok-industrial-c/generated/fidelity_qa.json'
    $qaData=Get-Content -LiteralPath $qa -Raw | ConvertFrom-Json
    if($qaData.region -ne 'bialystok-industrial-c' -or ($qaData.summary | ConvertTo-Json -Depth 100 -Compress) -ne ($fidelity | ConvertTo-Json -Depth 100 -Compress)){throw 'Fidelity summary/QA mismatch'}
    $qaCopy=Join-Path $PSScriptRoot 'fidelity/fidelity_qa.json'
    Copy-Item -LiteralPath $qa -Destination $qaCopy -Force
    $qaSha=(Get-FileHash -LiteralPath $qa).Hash.ToLowerInvariant()
    if((Get-FileHash -LiteralPath $qaCopy).Hash.ToLowerInvariant() -ne $qaSha){throw 'Fidelity QA copy differs'}
    $audit=Get-Content (Join-Path $PSScriptRoot 'AUDIT.json') -Raw | ConvertFrom-Json
    if($audit.status -ne 'VERIFIED' -or $audit.raw_count -ne 168 -or $audit.sheet_count -ne 268){throw 'Incomplete evidence audit'}
    [ordered]@{status='VERIFIED';recorded_at=(Get-Date -Format o);source_head=(& git rev-parse HEAD).Trim();heavy_released=$true;gis_passed=$counts.passed;gis_failed=0;gis_xfailed=$counts.xfailed;gis_skipped=$counts.skipped;gis_duration_seconds=$seconds;gis_summary=$line;gis_log_sha256=(Get-FileHash -LiteralPath $log).Hash.ToLowerInvariant();receipt_sha256=$bindings;fidelity_summary_sha256=(Get-FileHash (Join-Path $PSScriptRoot 'fidelity/fidelity_summary.json')).Hash.ToLowerInvariant();fidelity_qa_sha256=$qaSha;audit_sha256=(Get-FileHash (Join-Path $PSScriptRoot 'AUDIT.json')).Hash.ToLowerInvariant();note='Successful execution and evidence integrity; not a fidelity, D51, world or GPU budget PASS.'} | ConvertTo-Json -Depth 12 | Set-Content (Join-Path $PSScriptRoot 'validation-summary.json') -Encoding utf8
} finally {Pop-Location}
