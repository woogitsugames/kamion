param([Parameter(Mandatory=$true)][string]$RootRelease)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
function Assert-Slot {
 $invalid='artifacts/car-paint-r1/r4-release-invalidated.json'
 if(Test-Path $invalid){$r=Get-Content $invalid -Raw|ConvertFrom-Json;if($r.root_release-eq$RootRelease){throw 'Release invalidated; explicit fresh ROOT release required'}}
 foreach($name in @('PHONE_RUN','GPT_UNITY_HOLD')){if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/$name"){@{root_release=$RootRelease;marker=$name}|ConvertTo-Json|Set-Content $invalid -Encoding utf8;throw "$name active; stop"}}
}
try {
 Assert-Slot
 $log=[IO.Path]::GetFullPath('artifacts/car-paint-r1/r4-plate-editmode.log')
 $xml=[IO.Path]::GetFullPath('artifacts/car-paint-r1/r4-plate-editmode.xml')
 $code=Invoke-UnityBatch -NoQuit -LogFile $log -Arguments @('-runTests','-testPlatform','EditMode','-testFilter','Game.Tests.CarPlatePayloadTests','-testResults',$xml)
 if($code-ne0 -or -not(Test-Path $xml)){throw "Filtered EditMode exit=$code or missing XML; inspect log"}
 [xml]$result=Get-Content $xml
 if([int]$result.'test-run'.total-lt6 -or [int]$result.'test-run'.failed-ne0){throw 'Filtered native plate suite failed or incomplete'}
} finally {git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting}
