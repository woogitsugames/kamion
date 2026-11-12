$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
$source=$PSScriptRoot
$destination='C:\Users\matma\Documents\Claude\kamion\artifacts\landmarks-r3'
Set-Location (Split-Path (Split-Path $source))
if((& git branch --show-current).Trim() -ne 'gpt-landmarks-r3'){throw 'Unexpected branch'}
if(-not (Test-Path "$source/REPORT.md")){throw 'Missing final REPORT'}
$validation=Get-Content "$source/final-python-result.json" -Raw | ConvertFrom-Json
$edit=Get-Content "$source/editmode-result.json" -Raw | ConvertFrom-Json
if(-not $validation.complete -or $validation.cache_exit -ne 0 -or $edit.failed -ne 0){throw 'Incomplete validation'}
& robocopy $source $destination /E /R:2 /W:1 /NFL /NDL /NP /LOG:"$source/robocopy-main.log"
$code=$LASTEXITCODE
if($code -gt 7){throw "robocopy failed: $code"}
$counts=@{}
$verified=0
foreach($condition in @('Low-overcast','Low-clear','High-overcast','High-clear')){
    $frames=@(Get-ChildItem "$source/after-corrected/$condition" -Filter '*.png')
    if($frames.Count -ne 61){throw "Unexpected frame count $condition"}
    foreach($frame in $frames){
        $other=Join-Path $destination "after-corrected/$condition/$($frame.Name)"
        if((Get-FileHash $frame.FullName).Hash -ne (Get-FileHash $other).Hash){throw "Frame mismatch $condition/$($frame.Name)"}
        $verified++
    }
    $counts[$condition]=$frames.Count
}
$reportHash=(Get-FileHash "$source/REPORT.md").Hash
if($reportHash -ne (Get-FileHash "$destination/REPORT.md").Hash){throw 'Report mismatch'}
@{branch='gpt-landmarks-r3';source_validation_commit='b4da1f8e';time_local=(Get-Date).ToString('o');
    robocopy_exit=$code;verified_final_frames=$verified;after_corrected_frames=$counts;
    report_sha256=$reportHash;main_report_verified=$true;no_main_commit=$true} |
    ConvertTo-Json -Depth 5 | Set-Content "$source/COPY-RECEIPT.json" -Encoding utf8
Copy-Item -LiteralPath "$source/COPY-RECEIPT.json" -Destination "$destination/COPY-RECEIPT.json"
Write-Host "Copied r3: $verified final frames and REPORT verified; robocopy=$code"
exit 0
