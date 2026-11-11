param([ValidateSet('All','Low','High')][string]$OnlyTier='All',[ValidateSet('All','clear','overcast')][string]$OnlyLight='All',[switch]$ReplaySignalStart)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
function Guard {if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity hold returned; a new explicit ROOT release is required'}}
$shader=Join-Path $RepoRoot 'game/Assets/_Project/Environment/Shaders/WorldPBR.shader'
$sourceSHA=(Get-FileHash -LiteralPath $shader -Algorithm SHA256).Hash
if($sourceSHA-ne'1DC7DB4EA4EC839F4DC8FBD301BA5AEDD38A12C3FFF892E66818841D125EDCE4'){throw 'Production shader is not the selected exact source'}
$protected=@{}
foreach($id in @('road_asphalt','road_asphalt_new','marking_white')){
 $file=Join-Path $RepoRoot "game/Assets/_Generated/World/bialystok-industrial-c/Materials/M_$id.mat";$protected[$file]=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash
}
if($ReplaySignalStart){
 $delta=Get-Content -LiteralPath artifacts/surface-wear-r1/wear-probe-signal-material-delta.json -Raw | ConvertFrom-Json
 foreach($row in $delta.changes){$original=Join-Path (Join-Path $PSScriptRoot 'bus-only-canonical') $row.file;if((Get-FileHash -LiteralPath $original -Algorithm SHA256).Hash-ne$row.initial_sha256){throw 'Initial signal SHA mismatch'};Copy-Item -LiteralPath $original -Destination (Join-Path $RepoRoot $row.file)}
}
foreach($tier in @('Low','High')){foreach($light in @('clear','overcast')){
 if($OnlyTier-ne'All'-and$tier-ne$OnlyTier){continue};if($OnlyLight-ne'All'-and$light-ne$OnlyLight){continue}
 Guard
 $scene=if($tier-eq'High'){'WorldC_High'}else{'WorldC'}
 $log=Join-Path $RepoRoot "artifacts/surface-wear-r1/packed-mask-$tier-$light.log"
 $output=Join-Path $RepoRoot "artifacts/surface-wear-r1/packed-mask-qa/$tier-$light"
 $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','SurfaceWearQA.PackedMaskQA.Render','-qaScene',$scene,'-qaTier',$tier,'-qaLighting',$light,'-qaCameras','d_wear_lane_old,d_wear_missing_uv_2,d_wear_newroad_negative,d_field_p8_turn','-qaGate3',(Join-Path $RepoRoot 'artifacts/surface-wear-r1/qa-packed-mask-cameras.json'),'-qaOutput',$output)
 Show-UnityLogErrors $log
 if($code-ne0 -or -not(Select-String -Path $log -SimpleMatch 'PACKED_MASK_RENDERED: OK frames=4' -Quiet) -or -not(Select-String -Path $log -SimpleMatch 'PACKED_MASK_RESTORED:' -Quiet)){throw "Packed-mask diagnostic failed $tier $light with exit $code"}
 if((Get-FileHash -LiteralPath $shader -Algorithm SHA256).Hash-ne$sourceSHA){throw 'Production shader changed'}
 foreach($file in $protected.Keys){if((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash-ne$protected[$file]){throw "Production material changed: $file"}}
 git restore -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings/QualitySettings.asset
}}
