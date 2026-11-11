param([Parameter(Mandatory=$true)][string]$RootRelease,[string]$Round='r4-focus-r1')
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
function Assert-Slot {
 if(Test-Path artifacts/car-paint-r1/r4-release-invalidated.json){$r=Get-Content artifacts/car-paint-r1/r4-release-invalidated.json -Raw|ConvertFrom-Json;if($r.root_release-eq$RootRelease){throw 'Release invalidated; fresh ROOT release required'}}
 foreach($name in @('PHONE_RUN','GPT_UNITY_HOLD')){if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/$name"){throw "$name active; stop before launch"}}
}
$ids='r10_wheel_02,r10_front_04,r10_rear_04,r10b_black_05,g_current_black_wheel_02,g_dirt_level_0,g_dirt_level_1,g_dirt_level_2,g_dirt_level_3,r4_dirt_candidate_3'
$env:KAMION_G_SOURCE_HEAD=(& git rev-parse HEAD).Trim()
$env:KAMION_G_SOURCE_PROOF_SHA=(Get-FileHash artifacts/car-paint-r1/r4-candidate-r1-imported-source-proof.json).Hash
try {
 foreach($tier in @('Low','High')){foreach($light in @('clear','overcast')){
  Assert-Slot
  $out="artifacts/car-paint-r1/$Round/$tier-$light"
  if(Test-Path $out){throw "Refuse overwrite $out"}
  $env:KAMION_G_POSE_OUTPUT=[IO.Path]::GetFullPath("$out/poses")
  $scene=if($tier-eq'High'){'WorldC_High'}else{'WorldC'}
  try {
   & pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $light -Gate3 artifacts/car-paint-r1/r4-baseline-cameras.json -Cameras $ids -OutputDir $out *> "artifacts/car-paint-r1/$Round-$tier-$light-wrapper.log"
   if($LASTEXITCODE-ne0){throw "Focus failed $tier $light"}
  }finally{git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting}
 }}
}finally{
 Remove-Item Env:KAMION_G_POSE_OUTPUT -ErrorAction SilentlyContinue
 Remove-Item Env:KAMION_G_SOURCE_HEAD -ErrorAction SilentlyContinue
 Remove-Item Env:KAMION_G_SOURCE_PROOF_SHA -ErrorAction SilentlyContinue
}
