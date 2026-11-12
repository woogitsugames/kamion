param([Parameter(Mandatory)][ValidatePattern('^[a-z0-9-]+$')][string]$Stage)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
$library='art-source/world/props/street_props.glb'
@{stage=$Stage;time=(Get-Date).ToString('o');library_sha=(Get-FileHash $library).Hash;meta_sha=(Get-FileHash art-source/world/props/props_meta.json).Hash;cameras_sha=(Get-FileHash artifacts/life-r2/cameras.json).Hash;probe_sha=(Get-FileHash game/Assets/_Project/Editor/VisualQA/LifeExactStats.cs).Hash} | ConvertTo-Json | Set-Content "artifacts/life-r2/$Stage-inputs.json"
foreach($tier in @('Low','High')) { foreach($light in @('clear','overcast')) {
 $scene=if($tier -eq 'High'){'WorldC_High'}else{'WorldC'}
 $dir=[IO.Path]::GetFullPath("artifacts/life-r2/$Stage/$tier-$light")
 if(Test-Path -LiteralPath $dir){throw "Evidence exists: $dir"}
 New-Item -ItemType Directory -Path $dir | Out-Null
 $log=[IO.Path]::GetFullPath("artifacts/life-r2/$Stage-$tier-$light.log")
 & pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner gpt-life -StaleHours 1000000
 if($LASTEXITCODE -ne 0){throw 'Unity slot unavailable'}
 try {
  $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.VisualQaRunner.RenderControlCameras','-qaScene',$scene,'-qaWidth','2340','-qaHeight','1080','-qaTier',$tier,'-qaOutput',$dir,'-qaLighting',$light,'-qaGate3',[IO.Path]::GetFullPath('artifacts/life-r2/cameras.json'),'-qaLifeExact',(Join-Path $dir 'exact-stats.json'))
  if($code -ne 0){throw "Exact capture failed: $tier $light ($code)"}
  if(!(Test-Path -LiteralPath (Join-Path $dir 'exact-stats.json'))){throw 'Exact probe produced no evidence'}
 } finally {
  & pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner gpt-life
  git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
 }
}}
