$ErrorActionPreference='Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
$started=Get-Date
& pwsh artifacts/landmarks-r2/unity-step.ps1 -Step EditMode
$code=$LASTEXITCODE
$xml=Get-ChildItem artifacts/tests -Filter 'editmode-*.xml' | Where-Object {$_.LastWriteTime -ge $started.AddSeconds(-1)} | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if(-not $xml){throw 'Missing current EditMode XML'}
Copy-Item -LiteralPath $xml.FullName -Destination "$PSScriptRoot/EditMode-final.xml"
[xml]$doc=Get-Content "$PSScriptRoot/EditMode-final.xml" -Raw
$run=$doc.'test-run'
@{exit=$code;total=[int]$run.total;passed=[int]$run.passed;failed=[int]$run.failed;skipped=[int]$run.skipped;result=[string]$run.result} | ConvertTo-Json | Set-Content -Encoding utf8 "$PSScriptRoot/editmode-result.json"
exit $code
