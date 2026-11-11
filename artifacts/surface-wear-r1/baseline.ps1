param([ValidateSet('Import','Fixtures','Capture')][string]$Phase)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
function Guard { if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity hold returned; no transient auto-resume'} }
function RestoreOwned { git restore -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings/QualitySettings.asset }
if($Phase-eq'Import') {
 Guard
 # Ownworld/PBRalreadyfresh+SHAverified. Invokeonlycanonicalimportentrypoint, avoidingredundantfetch/build/unguardedlateUnitylaunch.
 $log=Join-Path $RepoRoot 'artifacts/surface-wear-r1/baseline-import.log'
 $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.World.Import.RegionImporter.ImportBatch','-region','bialystok-industrial-c','-tiers','Low,High','-materialTier','Medium')
 Show-UnityLogErrors $log
 if($code-ne0 -or -not(Select-String -Path $log -SimpleMatch 'IMPORT_RESULT: OK' -Quiet)){throw "Pristinebaselineimportfailedexit$code"}
 RestoreOwned
}
if($Phase-eq'Fixtures') {
 foreach($step in @(@{id='truck';method='Game.Editor.Setup.TruckAssetBuilder.BuildBatch';ok='TRUCK_RESULT: OK'},@{id='trailer';method='Game.Editor.Setup.TrailerAssetBuilder.BuildBatch';ok='TRAILER_RESULT: OK'},@{id='install';method='Game.World.Import.WorldTruckInstaller.InstallBatch';ok='TRUCK_RESULT: OK'})){
  Guard
  $log=Join-Path $RepoRoot ('artifacts/surface-wear-r1/baseline-'+$step.id+'.log')
  $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod',$step.method)
  Show-UnityLogErrors $log
  if($code-ne0 -or -not(Select-String -Path $log -SimpleMatch $step.ok -Quiet)){throw "Pristinefixturefailed$($step.id)exit$code"}
  RestoreOwned
 }
}
if($Phase-eq'Capture') {
 foreach($tier in @('Low','High')){foreach($light in @('clear','overcast')){
  Guard
  $scene=if($tier-eq'High'){'WorldC_High'}else{'WorldC'}
  pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $light -Gate3 artifacts/surface-wear-r1/qa-cameras.json -OutputDir "artifacts/surface-wear-r1/before/$tier-$light"
  if($LASTEXITCODE-ne0){throw "Pristinecapturefailed$tier$light"}
  RestoreOwned
 }}
}
