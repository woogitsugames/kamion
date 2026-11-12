$ErrorActionPreference='Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
$record=Get-Content "$PSScriptRoot/FINAL-CANDIDATE.json" -Raw | ConvertFrom-Json
if(-not $record.visual_review_complete -or $record.camera_conditions -ne 244){throw 'Full review not recorded'}
if(@($record.renderer_input_sha256.PSObject.Properties).Count -lt 7){throw 'Missing renderer bindings'}
foreach($entry in $record.renderer_input_sha256.PSObject.Properties){
    if((Get-FileHash -LiteralPath $entry.Name).Hash -ne $entry.Value){throw "Changed renderer input: $($entry.Name)"}
}
$started=Get-Date
& pwsh artifacts/landmarks-r4/unity-step.ps1 -Step EditMode
$code=$LASTEXITCODE
$xml=Get-ChildItem artifacts/tests -Filter 'editmode-*.xml' | Where-Object {$_.LastWriteTime -ge $started.AddSeconds(-1)} | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if(-not $xml){throw 'Missing current EditMode XML'}
Copy-Item -LiteralPath $xml.FullName -Destination "$PSScriptRoot/EditMode-final.xml"
[xml]$doc=Get-Content "$PSScriptRoot/EditMode-final.xml" -Raw
$run=$doc.'test-run'
@{exit=$code;total=[int]$run.total;passed=[int]$run.passed;failed=[int]$run.failed;skipped=[int]$run.skipped;result=[string]$run.result} |
    ConvertTo-Json | Set-Content "$PSScriptRoot/editmode-result.json" -Encoding utf8
exit $code
