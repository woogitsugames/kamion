param([Parameter(Mandatory=$true)][string]$RootRelease)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
function Assert-Slot {
 if(Test-Path artifacts/car-paint-r1/r4-release-invalidated.json){$r=Get-Content artifacts/car-paint-r1/r4-release-invalidated.json -Raw|ConvertFrom-Json;if($r.root_release-eq$RootRelease){throw 'Release invalidated'}}
 foreach($name in @('PHONE_RUN','GPT_UNITY_HOLD')){if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/$name"){throw "$name active; new ROOT release required"}}
}
Assert-Slot
foreach($name in @('R4CarFilmGpuProbe.cs','R4RearControls.cs')){Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path 'game/Assets/_Generated/Editor' $name)}
$env:KAMION_G_SOURCE_HEAD=(& git rev-parse HEAD).Trim()
$env:KAMION_G_SOURCE_PROOF_SHA=(Get-FileHash artifacts/car-paint-r1/r4-candidate-r1-imported-source-proof.json).Hash
try {
 Assert-Slot
 $log=[IO.Path]::GetFullPath('artifacts/car-paint-r1/r4-rear-controls.log')
 $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.R4RearControls.RunBatch','-qaGate3',[IO.Path]::GetFullPath('artifacts/car-paint-r1/r4-rear-control-camera.json'))
 if($code-ne0 -or -not(Select-String -Path $log -SimpleMatch 'R4_REAR_CONTROLS_RESULT: OK frames=20' -Quiet)){throw "Rear controls failed exit=$code; inspect log"}
}finally{
 git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting
 Remove-Item Env:KAMION_G_SOURCE_HEAD -ErrorAction SilentlyContinue
 Remove-Item Env:KAMION_G_SOURCE_PROOF_SHA -ErrorAction SilentlyContinue
}
