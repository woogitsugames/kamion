$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((git branch --show-current).Trim() -ne 'gpt-life-r4'){throw 'Wrong branch'}
. scripts/env.ps1
$proof=Get-Content artifacts/life-r4/before-inputs.json -Raw|ConvertFrom-Json
function Assert-Frozen {
 foreach($p in $proof.source_sha.PSObject.Properties){if((Get-FileHash $p.Name).Hash -ne $p.Value){throw "Baseline source changed: $($p.Name)"}}
 if((Get-FileHash art-source/world/props/street_props.glb).Hash -ne $proof.library_sha){throw 'Baseline GLB changed'}
 if((Get-FileHash art-source/world/props/props_meta.json).Hash -ne $proof.meta_sha){throw 'Baseline metadata changed'}
}
Assert-Frozen
$wanted=@(Get-Content artifacts/life-r2/yard-targets-v2.json -Raw|ConvertFrom-Json)
$found=@{}
$manifest=Get-Content Data/Regions/bialystok-industrial-c/generated/world_manifest.json -Raw|ConvertFrom-Json
foreach($chunk in $manifest.chunks){
 $instances=(Get-Content -LiteralPath $chunk.instances.file -Raw|ConvertFrom-Json).instances
 foreach($target in $wanted){
  foreach($item in $instances|Where-Object {$_.p -eq $target.p -and $_.src -eq $target.src}){
   if([math]::Abs($item.e-$target.e) -lt 0.001 -and [math]::Abs($item.n-$target.n) -lt 0.001 -and [math]::Abs($item.z-$target.z) -lt 0.001){
    if($found.ContainsKey($target.p)){throw 'Ambiguous generated target'}
    $found[$target.p]=$item
   }
  }
 }
}
if($found.Count -ne $wanted.Count){throw 'Historical yard targets changed; find fresh cameras before diagnostics'}
$targets=@(foreach($item in $wanted){@{prototype=$item.p;localPosition=@{x=$item.e;y=$item.z;z=$item.n}}})
@{targets=$targets}|ConvertTo-Json -Depth 5|Set-Content artifacts/life-r4/yard-native-targets.json
Copy-Item artifacts/life-r4/Life4YardLodProbe.cs game/Assets/_Generated/Editor/Life4YardLodProbe.cs
$ids=@($wanted|ForEach-Object {"yard_$($_.p)_side8"})
$selected=$ids -join ','
$result=@()
foreach($tier in @('Low','High')) {
 Assert-Frozen
 $scene=if($tier -eq 'High'){'WorldC_High'}else{'WorldC'}
 $dir=[IO.Path]::GetFullPath("artifacts/life-r4/baseline-lod/$tier-overcast")
 if(Test-Path $dir){throw 'Diagnostic evidence exists; inspect instead of overwrite'}
 $canonical=Get-Content "artifacts/life-r4/before/$tier-overcast/exact-stats.json" -Raw|ConvertFrom-Json
 New-Item -ItemType Directory -Path $dir|Out-Null
 & pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner gpt-life -StaleHours 1000000 -PollSeconds 1
 if($LASTEXITCODE){throw 'Unity acquire failed'}
 try {
  $code=Invoke-UnityBatch -LogFile "$dir/unity.log" -Arguments @('-executeMethod','Game.Editor.VisualQA.VisualQaRunner.RenderControlCameras',
   '-qaScene',$scene,'-qaWidth','2340','-qaHeight','1080','-qaTier',$tier,'-qaOutput',$dir,'-qaLighting','overcast',
   '-qaGate3',[IO.Path]::GetFullPath('artifacts/life-r4/cameras.json'),'-qaCameras',$selected,
   '-qaLifeExact',"$dir/exact-stats.json",'-qaLifeYardLod',"$dir/native-lod.json",'-qaLifeYardTargets',[IO.Path]::GetFullPath('artifacts/life-r4/yard-native-targets.json'))
  if($code){throw "Diagnostic Unity failed: $tier"}
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
 Add-Content artifacts/life-r4/STATUS.md "`nDiagnostyka LOD $tier zakończona: rzeczywiste bufory natywnej metody i liczniki/pozy identyczne z kanonicznym baseline, 5 celów. Następny krok: odczytać native-lod.json i obejrzeć koła, nie wnioskować z nazwy side8."
 git add -f artifacts/life-r4/STATUS.md "$dir/native-lod.json" "$dir/exact-stats.json"
 git commit -m "wip(life): potwierdź natywny LOD placu $tier"
 if($LASTEXITCODE){throw 'WIP failed'}
}
@{finished=(Get-Date -Format o);rows=$result}|ConvertTo-Json -Depth 8|Set-Content artifacts/life-r4/baseline-lod-result.json
