param([string]$Round='r2-focused')
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
foreach($tier in @('Low','High')) {
 foreach($light in @('clear','overcast')) {
  if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Shared Unity guard active; fresh explicit ROOT release required'}
  $scene=if($tier-eq'High'){'WorldC_High'}else{'WorldC'}
  try {
   & pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $light -Gate3 artifacts/car-paint-r1/r1-cameras.json -Cameras g_dirt_level_0,g_dirt_level_1,g_dirt_level_2,g_dirt_level_3,r10b_black_05,g_current_black_wheel_02 -OutputDir "artifacts/car-paint-r1/$Round/$tier-$light"
   if($LASTEXITCODE-ne0){throw "Focused R2 failed $tier $light"}
  } finally {git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting}
 }
}
