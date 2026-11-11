param([ValidateSet('Import','Capture')][string]$Phase)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
function Guard { if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity hold returned; explicit ROOT release required'} }
if($Phase-eq'Import') {
 Guard
 $log=Join-Path $RepoRoot 'artifacts/surface-wear-r1/uv-sentinel-import.log'
 $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.World.Import.RegionImporter.ImportBatch','-region','bialystok-industrial-c','-tiers','Low,High','-materialTier','Medium')
 Show-UnityLogErrors $log
 if($code-ne0 -or -not(Select-String -Path $log -SimpleMatch 'IMPORT_RESULT: OK' -Quiet)){throw "Sentinel import failed exit $code"}
 git restore -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings/QualitySettings.asset
}
if($Phase-eq'Capture') {
 foreach($tier in @('Low','High')) {foreach($light in @('clear','overcast')) {
 Guard
 $scene=if($tier-eq'High'){'WorldC_High'}else{'WorldC'}
 pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $light -Cameras 'd_wear_missing_uv_1,d_wear_missing_uv_2,d_wear_newroad_negative' -Gate3 artifacts/surface-wear-r1/qa-cameras.json -OutputDir "artifacts/surface-wear-r1/uv-sentinel/$tier-$light"
 if($LASTEXITCODE-ne0){throw "Sentinel capture failed $tier $light"}
 git restore -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings/QualitySettings.asset
 }}
}
