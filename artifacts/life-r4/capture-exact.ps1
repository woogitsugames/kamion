param([Parameter(Mandatory)][ValidatePattern('^[a-z0-9-]+$')][string]$Stage)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
$library='art-source/world/props/street_props.glb'
$sceneControls=[ordered]@{}
foreach($name in @('WorldC','WorldC_High')) {
 $scenePath="game/Assets/_Generated/World/bialystok-industrial-c/$name.unity"
 $ids=@(foreach($block in [regex]::Split((Get-Content $scenePath -Raw),'(?m)^--- ')) {
  if($block.Contains('guid: 19f8eede768d66b4f97dd76f3446dd69')) {
   $match=[regex]::Match($block,'(?m)^  id: (.+)\r?$')
   if(!$match.Success){throw 'Unnamed native scene control camera'}
   $match.Groups[1].Value.Trim()
  }
 })
 if($ids.Count -lt 40){throw 'Incomplete scene camera inventory'}
 $sceneControls[$name]=@{ids=$ids;scene_sha=(Get-FileHash $scenePath).Hash}
}
$sourceHashes=[ordered]@{}
foreach($source in @('tools/worldgen/streetscape/life.py','tools/worldgen/streetscape/life_props.py','tools/worldgen/streetscape/life_cars.py','tools/worldgen/streetscape/depot_yard.py','tools/worldgen/streetscape/materials.py','game/Assets/_Project/Environment/Shaders/WorldPBR.shader','game/Assets/_Project/World/Import/WorldPbrMaterials.cs')){$sourceHashes[$source]=(Get-FileHash -LiteralPath $source).Hash}
$libraryHash=(Get-FileHash $library).Hash
$metaHash=(Get-FileHash art-source/world/props/props_meta.json).Hash
$cameraHash=(Get-FileHash artifacts/life-r4/cameras.json).Hash
function Assert-FrozenInputs {
 foreach($entry in $sourceHashes.GetEnumerator()) {
  if((Get-FileHash -LiteralPath $entry.Key).Hash -ne $entry.Value){throw "Source changed during capture: $($entry.Key)"}
 }
 if((Get-FileHash $library).Hash -ne $libraryHash -or (Get-FileHash art-source/world/props/props_meta.json).Hash -ne $metaHash){throw 'Library changed during capture'}
 if((Get-FileHash artifacts/life-r4/cameras.json).Hash -ne $cameraHash){throw 'Camera packet changed during capture'}
}
@{stage=$Stage;time=(Get-Date).ToString('o');source_commit=(git rev-parse HEAD);source_sha=$sourceHashes;library_sha=(Get-FileHash $library).Hash;meta_sha=(Get-FileHash art-source/world/props/props_meta.json).Hash;cameras_sha=(Get-FileHash artifacts/life-r4/cameras.json).Hash;probe_sha=(Get-FileHash game/Assets/_Project/Editor/VisualQA/LifeExactStats.cs).Hash;scene_controls=$sceneControls} | ConvertTo-Json -Depth 6 | Set-Content "artifacts/life-r4/$Stage-inputs.json"
foreach($tier in @('Low','High')) { foreach($light in @('clear','overcast')) {
 Assert-FrozenInputs
 $scene=if($tier -eq 'High'){'WorldC_High'}else{'WorldC'}
 $dir=[IO.Path]::GetFullPath("artifacts/life-r4/$Stage/$tier-$light")
 if(Test-Path -LiteralPath $dir){throw "Evidence exists: $dir"}
 New-Item -ItemType Directory -Path $dir | Out-Null
 $log=[IO.Path]::GetFullPath("artifacts/life-r4/$Stage-$tier-$light.log")
 & pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner gpt-life -StaleHours 1000000
 if($LASTEXITCODE -ne 0){throw 'Unity slot unavailable'}
 try {
  $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.VisualQaRunner.RenderControlCameras','-qaScene',$scene,'-qaWidth','2340','-qaHeight','1080','-qaTier',$tier,'-qaOutput',$dir,'-qaLighting',$light,'-qaGate3',[IO.Path]::GetFullPath('artifacts/life-r4/cameras.json'),'-qaLifeExact',(Join-Path $dir 'exact-stats.json'))
  if($code -ne 0){throw "Exact capture failed: $tier $light ($code)"}
  if(!(Test-Path -LiteralPath (Join-Path $dir 'exact-stats.json'))){throw 'Exact probe produced no evidence'}
 } finally {
  & pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner gpt-life
  git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
 }
 Assert-FrozenInputs
}}

