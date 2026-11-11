$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Shared Unity guard active; NEW explicit ROOT release required'}
$started=Get-Date
try {
 & pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/test.ps1 -Platform EditMode
 $exit=$LASTEXITCODE
 $xml=Get-ChildItem artifacts/tests/editmode-*.xml | Where-Object {$_.LastWriteTime-ge$started} | Sort-Object LastWriteTime -Descending | Select-Object -First 1
 if($null-eq$xml){throw 'Fresh EditMode XML missing'}
 Copy-Item -LiteralPath $xml.FullName artifacts/car-paint-r1/final-editmode.xml
 if($exit-ne0){throw "EditMode wrapper failed exit=$exit; inspect fresh XML/log"}
 [xml]$result=Get-Content -LiteralPath $xml.FullName
 if([int]$result.'test-run'.failed-ne0 -or [int]$result.'test-run'.total-eq0){throw 'EditMode suite not green'}
} finally {git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting}
