$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
foreach($tier in @('Low','High')) {
 foreach($light in @('clear','overcast')) {
  if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Shared Unity guard active'}
  $scene=if($tier-eq'High'){'WorldC_High'}else{'WorldC'}
  & pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $light -Cameras g_current_black_wheel_02 -Gate3 artifacts/car-paint-r1/wheel-cameras.json -OutputDir "artifacts/car-paint-r1/before-wheel/$tier-$light"
  if($LASTEXITCODE-ne0){throw 'Wheel baseline failed'}
  git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting
 }
}
