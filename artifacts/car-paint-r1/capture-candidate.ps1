param([string]$Round='r1')
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
foreach($tier in @('Low','High')) {
 foreach($light in @('clear','overcast')) {
  if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Shared Unity guard active'}
  $scene=if($tier-eq'High'){'WorldC_High'}else{'WorldC'}
  & pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $light -Gate3 artifacts/car-paint-r1/r1-cameras.json -OutputDir "artifacts/car-paint-r1/$Round/$tier-$light"
  if($LASTEXITCODE-ne0){throw "Candidate capture failed $tier $light"}
  git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting
 }
}
