param([ValidateSet('Low','High')][string[]]$Tiers=@('Low','High'),[ValidatePattern('^[a-z0-9-]*$')][string]$Suffix='')
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((git branch --show-current).Trim() -ne 'gpt-life-r5'){throw 'Wrong branch'}
. scripts/env.ps1
$proof=Get-Content artifacts/life-r5/before-inputs.json -Raw|ConvertFrom-Json
function Assert-Frozen {
 foreach($p in $proof.source_sha.PSObject.Properties){if((Get-FileHash $p.Name).Hash -ne $p.Value){throw "Baseline source changed: $($p.Name)"}}
 if((Get-FileHash art-source/world/props/street_props.glb).Hash -ne $proof.library_sha){throw 'Baseline GLB changed'}
 if((Get-FileHash art-source/world/props/props_meta.json).Hash -ne $proof.meta_sha){throw 'Baseline metadata changed'}
 if((Get-FileHash artifacts/life-r5/cameras.json).Hash -ne $proof.cameras_sha){throw 'Baseline camera packet changed'}
 foreach($scene in $proof.scene_controls.PSObject.Properties){
  $path="game/Assets/_Generated/World/bialystok-industrial-c/$($scene.Name).unity"
  if((Get-FileHash $path).Hash -ne $scene.Value.scene_sha){throw "Diagnostic changed saved scene: $path"}
 }
}
Assert-Frozen
$selection=Get-Content artifacts/life-r5/pallet-targets.json -Raw|ConvertFrom-Json
$entries=@($selection.selected)+@($selection.controls)
$wanted=@($entries|ForEach-Object {$_.instance})
$found=@{}
$manifest=Get-Content Data/Regions/bialystok-industrial-c/generated/world_manifest.json -Raw|ConvertFrom-Json
foreach($chunk in $manifest.chunks){
 $instances=(Get-Content -LiteralPath $chunk.instances.file -Raw|ConvertFrom-Json).instances
 foreach($target in $wanted){
  foreach($item in $instances|Where-Object {$_.p -eq $target.p -and $_.src -eq $target.src}){
   if([math]::Abs($item.e-$target.e) -lt .001 -and [math]::Abs($item.n-$target.n) -lt .001 -and [math]::Abs($item.z-$target.z) -lt .001){
    if($found.ContainsKey($target.p)){throw 'Ambiguous generated target'}
    $found[$target.p]=$item
   }
  }
 }
}
if($found.Count -ne $wanted.Count){throw 'Fresh pallet targets changed'}
$targets=@(foreach($item in $wanted){@{prototype=$item.p;localPosition=@{x=$item.e;y=$item.z;z=$item.n}}})
@{targets=$targets}|ConvertTo-Json -Depth 5|Set-Content artifacts/life-r5/yard-native-targets.json
Copy-Item artifacts/life-r5/Life5PropLodProbe.cs game/Assets/_Generated/Editor/Life5PropLodProbe.cs
$probeHash=(Get-FileHash artifacts/life-r5/Life5PropLodProbe.cs).Hash
$ids=@($entries|ForEach-Object {$_.cameras}|ForEach-Object {$_.id})
$selected=$ids -join ','
$result=@()
foreach($tier in $Tiers) {
 Assert-Frozen
 if((Get-FileHash game/Assets/_Generated/Editor/Life5PropLodProbe.cs).Hash -ne $probeHash){throw 'Installed diagnostic probe changed'}
 $scene=if($tier -eq 'High'){'WorldC_High'}else{'WorldC'}
 $extra=if($Suffix){"-$Suffix"}else{''}
 $dir=[IO.Path]::GetFullPath("artifacts/life-r5/baseline-lod/$tier-overcast$extra")
 if(Test-Path $dir){throw 'Diagnostic evidence exists; inspect instead of overwrite'}
 $canonical=Get-Content "artifacts/life-r5/before/$tier-overcast/exact-stats.json" -Raw|ConvertFrom-Json
 New-Item -ItemType Directory -Path $dir|Out-Null
 & pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner gpt-life -StaleHours 1000000 -PollSeconds 1
 if($LASTEXITCODE){throw 'Unity acquire failed'}
 try {
  $code=Invoke-UnityBatch -LogFile "$dir/unity.log" -Arguments @('-executeMethod','Game.Editor.VisualQA.VisualQaRunner.RenderControlCameras',
   '-qaScene',$scene,'-qaWidth','2340','-qaHeight','1080','-qaTier',$tier,'-qaOutput',$dir,'-qaLighting','overcast',
   '-qaGate3',[IO.Path]::GetFullPath('artifacts/life-r5/cameras.json'),'-qaCameras',$selected,
   '-qaLifeExact',"$dir/exact-stats.json",'-qaLifeYardLod',"$dir/native-lod.json",'-qaLifeYardTargets',[IO.Path]::GetFullPath('artifacts/life-r5/yard-native-targets.json'))
  @{tier=$tier;exit_code=$code;finished=(Get-Date -Format o);probe_sha=$probeHash}|ConvertTo-Json|Set-Content "$dir/unity-result.json"
  if($code){throw "Diagnostic Unity failed: $tier ($code)"}
 } finally {
  & pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner gpt-life
  git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
 }
 Assert-Frozen
 $dump=Get-Content "$dir/native-lod.json" -Raw|ConvertFrom-Json
 $exact=Get-Content "$dir/exact-stats.json" -Raw|ConvertFrom-Json
 if($dump.errors.Count -or $exact.errors.Count -or $dump.rows.Count -ne $ids.Count -or $exact.rows.Count -ne $ids.Count){throw 'Diagnostic incomplete or errored'}
 foreach($id in $ids){
  $a=@($canonical.rows|Where-Object id -eq $id);$b=@($exact.rows|Where-Object id -eq $id)
  if($a.Count -ne 1 -or $b.Count -ne 1){throw "Missing canonical/diagnostic camera $id"}
  foreach($field in @('worldTriangles','instanceTriangles','worldDraws','instanceDraws','objects','instances','cells','hlodCells','aspect','fov','orthographic','orthographicSize')){
   if($a[0].$field -ne $b[0].$field){throw "Dispatch parity mismatch: $tier $id $field"}
  }
  foreach($field in @('position','rotation')){
   if(($a[0].$field|ConvertTo-Json -Compress) -ne ($b[0].$field|ConvertTo-Json -Compress)){throw "Pose parity mismatch: $id"}
  }
 }
 $result+=@{tier=$tier;rows=$dump.rows.Count;dispatch_parity=$true;lods=$dump.rows|Select-Object camera,observedLods,distance,meshTriangles}
 Add-Content artifacts/life-r5/STATUS.md "`nDiagnostyka LOD $tier zakończona: rzeczywiste bufory natywnej metody i liczniki/pozy identyczne z kanonicznym baseline, $($ids.Count) kamer / cele palet i kontrole. Następny krok: odczytać native-lod.json i obejrzeć palety, nie wnioskować z nazwy prop_side3."
 git add -f artifacts/life-r5/STATUS.md "$dir/native-lod.json" "$dir/exact-stats.json"
 git commit -m "wip(life): potwierdź natywny LOD placu $tier"
 if($LASTEXITCODE){throw 'WIP failed'}
}
$extra=if($Suffix){"-$Suffix"}else{''}
@{finished=(Get-Date -Format o);rows=$result;probe_sha=$probeHash;saved_scenes_unchanged=$true}|ConvertTo-Json -Depth 8|Set-Content "artifacts/life-r5/baseline-lod-result$extra.json"
