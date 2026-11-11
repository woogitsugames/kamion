param([Parameter(Mandatory=$true)][string]$RootRelease)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
function Assert-Slot {
 $invalid='artifacts/car-paint-r1/r4-release-invalidated.json'
 if(Test-Path $invalid){$r=Get-Content $invalid -Raw|ConvertFrom-Json;if($r.root_release-eq$RootRelease){throw 'Release permanently invalidated'}}
 foreach($name in @('PHONE_RUN','GPT_UNITY_HOLD')){if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/$name"){@{root_release=$RootRelease;marker=$name}|ConvertTo-Json|Set-Content $invalid -Encoding utf8;throw "$name active"}}
}
$ids='r10_front_04,r10_rear_04,g_dirt_level_0,g_dirt_level_1,g_dirt_level_2,g_dirt_level_3,r4_rear_target_3'
Copy-Item artifacts/car-paint-r1/R4PosePacket.cs game/Assets/_Generated/Editor/R4PosePacket.cs
$env:KAMION_G_SOURCE_HEAD=(& git rev-parse HEAD).Trim()
$env:KAMION_G_SOURCE_PROOF_SHA=(Get-FileHash artifacts/car-paint-r1/r4-plate-r2-imported-source-proof.json).Hash
try {
 foreach($tier in @('Low','High')){foreach($light in @('clear','overcast')){
  $out="artifacts/car-paint-r1/r4-plate-focus/$tier-$light"
  if(Test-Path $out){throw "Refuse overwrite $out"}
  $env:KAMION_G_POSE_OUTPUT=[IO.Path]::GetFullPath("$out/poses")
  $scene=if($tier-eq'High'){'WorldC_High'}else{'WorldC'}
  Assert-Slot
  try {
   & pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $light -Gate3 artifacts/car-paint-r1/r4-plate-focus-cameras.json -Cameras $ids -OutputDir $out *> "artifacts/car-paint-r1/r4-plate-focus-$tier-$light-wrapper.log"
   if($LASTEXITCODE-ne0){throw "Plate focus failed $tier $light"}
  } finally {git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting}
 }}
} finally {Remove-Item Env:KAMION_G_POSE_OUTPUT,Env:KAMION_G_SOURCE_HEAD,Env:KAMION_G_SOURCE_PROOF_SHA -ErrorAction SilentlyContinue}
