$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
function Assert-Slot {
 if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Shared Unity guard active'}
}
Assert-Slot
$log=[IO.Path]::GetFullPath('artifacts/car-paint-r1/pearl-camera-prep.log')
$code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.GCameraPreparation.RunBatch')
if($code-ne0 -or -not(Select-String -Path $log -SimpleMatch 'G_CAMERA_PREP_RESULT: OK' -Quiet)){throw "Camera preparation failed $code"}
git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting
foreach($tier in @('Low','High')) {
 foreach($light in @('clear','overcast')) {
  Assert-Slot
  $scene=if($tier-eq'High'){'WorldC_High'}else{'WorldC'}
  & pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $light -Cameras r10b_black_05,g_current_black_wheel_02,g_current_black_lod_05,g_current_black_lod_20,g_current_black_lod_45 -Gate3 artifacts/car-paint-r1/pearl-cameras.json -OutputDir "artifacts/car-paint-r1/pearl-only/$tier-$light"
  if($LASTEXITCODE-ne0){throw 'Pearl-only capture failed'}
  git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting
 }
}
