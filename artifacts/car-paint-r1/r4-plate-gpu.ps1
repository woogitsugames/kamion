param([Parameter(Mandatory=$true)][string]$RootRelease)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
function Assert-Slot {
 $invalid='artifacts/car-paint-r1/r4-release-invalidated.json'
 if(Test-Path $invalid){$r=Get-Content $invalid -Raw|ConvertFrom-Json;if($r.root_release-eq$RootRelease){throw 'Release invalidated; new explicit release required'}}
 foreach($name in @('PHONE_RUN','GPT_UNITY_HOLD')){if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/$name"){@{root_release=$RootRelease;marker=$name}|ConvertTo-Json|Set-Content $invalid -Encoding utf8;throw "$name active"}}
}
Copy-Item artifacts/car-paint-r1/R4PlateGpuProbe.cs game/Assets/_Generated/Editor/R4PlateGpuProbe.cs
try {
 Assert-Slot
 $log=[IO.Path]::GetFullPath('artifacts/car-paint-r1/r4-plate-gpu.log')
 $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.R4PlateGpuProbe.RunBatch')
 if($code-ne0 -or -not(Select-String -Path $log -SimpleMatch 'R4_PLATE_GPU_RESULT: OK' -Quiet)){throw "Plate GPU diagnostic exit=$code; inspect log"}
} finally {git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting}
