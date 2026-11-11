param([ValidateSet('Import','Fixtures','Capture')][string]$Phase)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
function Assert-PhoneSlot {
 if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Main PHONE_RUN/GPT_UNITY_HOLD active; no Unity launch'}
}
function Restore-OwnedSideEffects {
 git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat
}
if($Phase-eq'Import') {
 Assert-PhoneSlot
 & pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/import-region.ps1 -Region bialystok-industrial-c
 if($LASTEXITCODE-ne0){throw 'Baseline import failed; inspect log before retry'}
 Restore-OwnedSideEffects
}
if($Phase-eq'Fixtures') {
 foreach($method in @('Game.Editor.Setup.TruckAssetBuilder.BuildBatch','Game.Editor.Setup.TrailerAssetBuilder.BuildBatch','Game.World.Import.WorldTruckInstaller.InstallBatch')) {
  Assert-PhoneSlot
  $tag=$method.Split('.')[-2]
  $log=[IO.Path]::GetFullPath("artifacts/car-paint-r1/baseline-$tag.log")
  $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod',$method)
  $ok=Select-String -Path $log -Pattern '^(TRUCK|TRAILER)_RESULT: OK' -Quiet
  if($code-eq-1073741819 -and $ok -and (Select-String -Path $log -SimpleMatch 'D3D12PipelineCacheLibrary::SaveCache' -Quiet)) {
   Write-Warning "Known post-completion D3D12 shutdown crash after $tag; explicit builder result OK retained in log"
   $code=0
  }
  if($code-ne0 -or -not$ok){throw "Fixture failed $tag exit=$code"}
  Restore-OwnedSideEffects
 }
 & uv run --project tools/worldgen python artifacts/car-paint-r1/proof.py baseline-canonical
 if($LASTEXITCODE-ne0){throw 'Canonical source proof failed'}
}
if($Phase-eq'Capture') {
 foreach($tier in @('Low','High')) {
  foreach($light in @('clear','overcast')) {
   Assert-PhoneSlot
   $scene=if($tier-eq'High'){'WorldC_High'}else{'WorldC'}
   & pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $light -Gate3 artifacts/car-paint-r1/qa-cameras.json -OutputDir "artifacts/car-paint-r1/before/$tier-$light"
   if($LASTEXITCODE-ne0){throw "Baseline capture failed $tier $light"}
   Restore-OwnedSideEffects
  }
 }
}
