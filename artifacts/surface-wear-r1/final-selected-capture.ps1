param([ValidateSet('All','Primary','Legacy')][string]$Scope='All',[ValidateSet('All','Low','High')][string]$Tier='All',[ValidateSet('All','clear','overcast')][string]$Light='All',[switch]$ReplaySignalStart)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
function Guard {
 if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity hold returned; a new explicit ROOT release is required'}
 if((Get-FileHash game/Assets/_Project/Environment/Shaders/WorldPBR.shader -Algorithm SHA256).Hash-ne'1DC7DB4EA4EC839F4DC8FBD301BA5AEDD38A12C3FFF892E66818841D125EDCE4'){throw 'Selected production shader changed'}
}
if($ReplaySignalStart){
 $delta=Get-Content artifacts/surface-wear-r1/wear-probe-signal-material-delta.json -Raw|ConvertFrom-Json
 foreach($row in $delta.changes){$src=Join-Path (Join-Path $PSScriptRoot 'bus-only-canonical') $row.file;if((Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash-ne$row.initial_sha256){throw 'Initial signal bytes mismatch'};Copy-Item -LiteralPath $src -Destination (Join-Path $RepoRoot $row.file)}
}
# Preserve the baseline ordering: all primary conditions, then all legacy conditions.
foreach($section in @('Primary','Legacy')){
 if($Scope-ne'All'-and$Scope-ne$section){continue}
 $ids=if($section-eq'Primary'){'capture-camera-ids.txt'}else{'legacy-camera-ids.txt'}
 $config=if($section-eq'Primary'){'qa-cameras.json'}else{'qa-cameras-legacy.json'}
 $stage=if($section-eq'Primary'){'after'}else{'after-legacy'}
 foreach($captureTier in @('Low','High')|Where-Object{$Tier-eq'All'-or$_-eq$Tier}){foreach($captureLight in @('clear','overcast')|Where-Object{$Light-eq'All'-or$_-eq$Light}){
  Guard
  $scene=if($captureTier-eq'High'){'WorldC_High'}else{'WorldC'}
  pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/visual-qa.ps1 -Scene $scene -Tier $captureTier -Lighting $captureLight -Cameras ((Get-Content (Join-Path $PSScriptRoot $ids) -Raw).Trim()) -Gate3 (Join-Path $PSScriptRoot $config) -OutputDir "artifacts/surface-wear-r1/$stage/$captureTier-$captureLight"
  if($LASTEXITCODE-ne0){throw "Final selected-source capture failed $section $captureTier $captureLight"}
  git restore -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings/QualitySettings.asset
 }}
}
