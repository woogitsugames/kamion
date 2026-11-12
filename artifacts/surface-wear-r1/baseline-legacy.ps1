param([string]$Stage='before-legacy',[ValidateSet('All','Low','High')][string]$Tier='All',[ValidateSet('All','clear','overcast')][string]$Light='All')
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
foreach($captureTier in @('Low','High')|Where-Object{$Tier-eq'All'-or$_-eq$Tier}){foreach($captureLight in @('clear','overcast')|Where-Object{$Light-eq'All'-or$_-eq$Light}){
 if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity hold returned; stop, noauto-resume'}
 $scene=if($captureTier-eq'High'){'WorldC_High'}else{'WorldC'}
 pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/visual-qa.ps1 -Scene $scene -Tier $captureTier -Lighting $captureLight -Cameras ((Get-Content artifacts/surface-wear-r1/legacy-camera-ids.txt -Raw).Trim()) -Gate3 artifacts/surface-wear-r1/qa-cameras-legacy.json -OutputDir "artifacts/surface-wear-r1/$Stage/$captureTier-$captureLight"
 if($LASTEXITCODE-ne0){throw "Legacynegativecapturefailed$captureTier$captureLight"}
 git restore -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings/QualitySettings.asset
}}
