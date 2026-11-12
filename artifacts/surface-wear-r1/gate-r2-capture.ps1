param([ValidateSet('All','Low','High')][string]$OnlyTier='All',[ValidateSet('All','clear','overcast')][string]$OnlyLight='All')
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
function Guard { if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity hold returned; explicit ROOT release required'} }
 foreach($tier in @('Low','High')) {foreach($light in @('clear','overcast')) {
 if($OnlyTier-ne'All'-and$tier-ne$OnlyTier){continue};if($OnlyLight-ne'All'-and$light-ne$OnlyLight){continue}
 Guard
 $scene=if($tier-eq'High'){'WorldC_High'}else{'WorldC'}
 pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $light -Cameras 'd_gate_pair_entry,d_gate_pair_exit,d_gate_kerb_nose,d_gate_kerb_outer' -Gate3 artifacts/surface-wear-r1/qa-gate-r2-cameras.json -OutputDir "artifacts/surface-wear-r1/gate-r2-after/$tier-$light"
 if($LASTEXITCODE-ne0){throw "Sentinel capture failed $tier $light"}
 git restore -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings/QualitySettings.asset
 }}
