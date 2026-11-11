$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
function Guard { if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity hold returned; explicit ROOT release required'} }
 foreach($tier in @('Low','High')) {foreach($light in @('clear','overcast')) {
 Guard
 $scene=if($tier-eq'High'){'WorldC_High'}else{'WorldC'}
 pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $light -Cameras 'd_gate_pair_entry,d_gate_pair_exit' -Gate3 artifacts/surface-wear-r1/qa-gate-pair-cameras.json -OutputDir "artifacts/surface-wear-r1/gate-pair-after/$tier-$light"
 if($LASTEXITCODE-ne0){throw "Sentinel capture failed $tier $light"}
 git restore -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings/QualitySettings.asset
 }}
