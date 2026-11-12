param([ValidateSet('All','Low','High')][string]$OnlyTier='All',[ValidateSet('All','clear','overcast')][string]$OnlyLight='All',[switch]$ReplaySignalStart,[switch]$SkipCompleted,[switch]$ActivationReplay)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
if($ActivationReplay-and($OnlyTier-ne'Low'-or$OnlyLight-ne'overcast'-or$ReplaySignalStart)){throw 'Activation verification is one identical Low-overcast replay without resetting signal startup'}
$prefix=if($ActivationReplay){'packed-mask-activation'}else{'packed-mask'}
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
 $runProof=Join-Path $PSScriptRoot "$prefix-$tier-$light-run.json"
 if($SkipCompleted-and(Test-Path -LiteralPath $runProof)){$previous=Get-Content -LiteralPath $runProof -Raw|ConvertFrom-Json;if($previous.complete){Write-Output "Already validated $tier $light; not repeating";continue}}
 Guard
 $scene=if($tier-eq'High'){'WorldC_High'}else{'WorldC'}
 $log=Join-Path $RepoRoot "artifacts/surface-wear-r1/$prefix-$tier-$light.log"
 $stage=if($ActivationReplay){'packed-mask-activation'}else{'packed-mask-qa'}
 $output=Join-Path $RepoRoot "artifacts/surface-wear-r1/$stage/$tier-$light"
 $runStart=Get-Date
 $qaArgs=@('-executeMethod','SurfaceWearQA.PackedMaskQA.Render','-qaScene',$scene,'-qaTier',$tier,'-qaLighting',$light,'-qaCameras','d_wear_lane_old,d_wear_missing_uv_2,d_wear_newroad_negative,d_field_p8_turn','-qaGate3',(Join-Path $RepoRoot 'artifacts/surface-wear-r1/qa-packed-mask-cameras.json'),'-qaOutput',$output)
 if($ActivationReplay){$qaArgs+=@('-qaActivation','1')}
 $code=Invoke-UnityBatch -LogFile $log -Arguments $qaArgs
 Show-UnityLogErrors $log
 $result=Select-String -Path $log -SimpleMatch 'PACKED_MASK_RENDERED: OK frames=4'|Select-Object -Last 1
 $restored=Select-String -Path $log -SimpleMatch 'PACKED_MASK_RESTORED:'|Select-Object -Last 1
 $fresh=@(Get-ChildItem -LiteralPath $output -Filter '*.png'|Where-Object{$_.LastWriteTime-ge$runStart}).Count
 $acceptedMono=$false
 if($code-ne0-and$result-and$restored-and$fresh-eq4){
  $mono=Select-String -Path $log -SimpleMatch 'Cleanup mono'|Where-Object{$_.LineNumber-gt$restored.LineNumber}|Select-Object -First 1
  $abort=Select-String -Path $log -SimpleMatch 'abort_threads: Failed aborting'|Where-Object{$_.LineNumber-gt$restored.LineNumber}|Select-Object -First 1
  $crash=Select-String -Path $log -Pattern 'Crash!!!|Obtained \d+ stack frames|Fatal Error|error CS\d+' -Quiet
  if($mono-and$abort-and-not$crash){$acceptedMono=$true;Write-Warning "Raw Unity exit $code after4freshframes and finallyrestore; accepted ADR0083 Mono cleanup only"}
 }
 if(($code-ne0-and-not$acceptedMono)-or-not$result-or-not$restored-or$fresh-ne4){throw "Packed-mask diagnostic failed $tier $light with exit $code"}
 @{complete=$true;tier=$tier;lighting=$light;raw_exit_code=$code;accepted_ADR0083_Mono_cleanup=$acceptedMono;fresh_frames=$fresh;finally_restored=$true;log_sha256=(Get-FileHash -LiteralPath $log -Algorithm SHA256).Hash}|ConvertTo-Json|Set-Content -LiteralPath $runProof -Encoding utf8
 if((Get-FileHash -LiteralPath $shader -Algorithm SHA256).Hash-ne$sourceSHA){throw 'Production shader changed'}
 foreach($file in $protected.Keys){if((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash-ne$protected[$file]){throw "Production material changed: $file"}}
 git restore -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings/QualitySettings.asset
}}
