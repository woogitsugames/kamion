param([Parameter(Mandatory=$true)][string]$RootRelease)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
$invalid='artifacts/car-paint-r1/r4-release-invalidated.json'
if(Test-Path $invalid){$r=Get-Content $invalid -Raw|ConvertFrom-Json;if($r.root_release-eq$RootRelease){throw 'Release invalidated'}}
foreach($name in @('PHONE_RUN','GPT_UNITY_HOLD')){if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/$name"){@{root_release=$RootRelease;marker=$name}|ConvertTo-Json|Set-Content $invalid -Encoding utf8;throw "$name active"}}
Copy-Item artifacts/car-paint-r1/R4PlateReplay.cs game/Assets/_Generated/Editor/R4PlateReplay.cs
Copy-Item artifacts/car-paint-r1/R4PosePacket.cs game/Assets/_Generated/Editor/R4PosePacket.cs
$env:KAMION_G_POSE_OUTPUT=[IO.Path]::GetFullPath('artifacts/car-paint-r1/r4-plate-pass-replay/init-poses')
$env:KAMION_G_SOURCE_HEAD=(&git rev-parse HEAD).Trim()
$env:KAMION_G_SOURCE_PROOF_SHA=(Get-FileHash artifacts/car-paint-r1/r4-plate-r3-imported-source-proof.json).Hash
try {
 foreach($name in @('PHONE_RUN','GPT_UNITY_HOLD')){if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/$name"){throw "$name active immediately before launch"}}
 $log=[IO.Path]::GetFullPath('artifacts/car-paint-r1/r4-plate-pass-replay.log')
 $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.R4PlateReplay.RunBatch','-qaGate3',[IO.Path]::GetFullPath('artifacts/car-paint-r1/r4-baseline-cameras.json'))
 if($code-ne0 -or -not(Select-String -Path $log -SimpleMatch 'R4_PLATE_REPLAY_RESULT: OK frames=2' -Quiet)){throw "Replay failed exit=$code"}
}finally{git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting;Remove-Item Env:KAMION_G_POSE_OUTPUT,Env:KAMION_G_SOURCE_HEAD,Env:KAMION_G_SOURCE_PROOF_SHA -ErrorAction SilentlyContinue}
