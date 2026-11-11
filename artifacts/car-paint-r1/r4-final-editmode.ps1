param([Parameter(Mandatory=$true)][string]$RootRelease)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
$invalid='artifacts/car-paint-r1/r4-release-invalidated.json'
if(Test-Path $invalid){$r=Get-Content $invalid -Raw|ConvertFrom-Json;if($r.root_release-eq$RootRelease){throw 'Release permanently invalidated'}}
try {
 foreach($name in @('PHONE_RUN','GPT_UNITY_HOLD')){if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/$name"){@{root_release=$RootRelease;marker=$name}|ConvertTo-Json|Set-Content $invalid -Encoding utf8;throw "$name active"}}
 $log=[IO.Path]::GetFullPath('artifacts/car-paint-r1/r4-final-editmode.log')
 $xml=[IO.Path]::GetFullPath('artifacts/car-paint-r1/r4-final-editmode.xml')
 $code=Invoke-UnityBatch -NoQuit -LogFile $log -Arguments @('-runTests','-testPlatform','EditMode','-testResults',$xml)
 if($code-ne0 -or -not(Test-Path $xml)){throw "Full EditMode failed exit=$code or XML missing"}
 [xml]$result=Get-Content $xml
 if([int]$result.'test-run'.total-lt200 -or [int]$result.'test-run'.failed-ne0){throw 'Full EditMode failed/incomplete'}
} finally {git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting}
