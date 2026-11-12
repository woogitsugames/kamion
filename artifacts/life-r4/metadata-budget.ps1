param([ValidatePattern('^[a-z0-9-]+$')][string]$Tag='a2')
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((git branch --show-current).Trim() -ne 'gpt-life-r4'){throw 'Wrong branch'}
$route=@((Get-Content artifacts/life-r4/route-camera-ids.json -Raw|ConvertFrom-Json).ids)
$scope=Get-Content "artifacts/life-r4/$Tag-wheel-scope.json" -Raw|ConvertFrom-Json
$counts=@{};foreach($m in $scope.static_counts){$counts[$m.node]=$m}
$result=@{};$bad=@();$checked=0
foreach($condition in @('Low-clear','Low-overcast','High-clear','High-overcast')){
 $before=Get-Content "artifacts/life-r4/before/$condition/exact-stats.json" -Raw|ConvertFrom-Json
 $after=Get-Content "artifacts/life-r4/after-$Tag/$condition/exact-stats.json" -Raw|ConvertFrom-Json
 if($before.errors.Count -or $after.errors.Count){throw 'Exact logger errors'}
 foreach($pair in @(@{dump=$before;field='before'},@{dump=$after;field='after'})){
  foreach($model in $pair.dump.models){
   for($lod=0;$lod -lt $model.triangles.Count;$lod++){
    $name=$model.name+$(if($lod){".lod$lod"}else{''})
    if(!$counts.ContainsKey($name) -or $model.triangles[$lod] -ne $counts[$name].($pair.field)){throw "Native mesh count differs from GLB: $condition $name"}
   }
  }
 }
 $old=@{};foreach($row in $before.rows){if($old.ContainsKey($row.id)){throw 'Duplicate before camera'};$old[$row.id]=$row}
 if($after.rows.Count -ne $old.Count){throw 'Camera count differs'}
 $rows=@()
 foreach($a in $after.rows){
  if(!$old.ContainsKey($a.id)){throw "Missing before camera $($a.id)"}
  $b=$old[$a.id]
  foreach($field in @('position','rotation','aspect','fov','orthographic','orthographicSize')){
   if(($a.$field|ConvertTo-Json -Compress) -ne ($b.$field|ConvertTo-Json -Compress)){throw "Pose/projection differs: $condition $($a.id) $field"}
  }
  $totalB=[long]$b.worldTriangles+[long]$b.instanceTriangles
  $totalA=[long]$a.worldTriangles+[long]$a.instanceTriangles
  $percent=100.0*($totalA-$totalB)/[math]::Max(1,$totalB)
  $world=$a.worldDraws-$b.worldDraws;$instance=$a.instanceDraws-$b.instanceDraws
  $isRoute=$a.id -in $route
  $rows+=@{camera=$a.id;is_route=$isRoute;total_before=$totalB;total_after=$totalA;
   tris_percent=$percent;world_draw_delta=$world;instance_draw_delta=$instance}
  if($world -gt 0 -or $instance -gt 0 -or ($isRoute -and $percent -gt 2)){$bad+=@{condition=$condition;camera=$a.id;tris_percent=$percent;world_draw_delta=$world;instance_draw_delta=$instance}}
 }
 $driving=@($rows|Where-Object is_route)
 if($driving.Count -ne $route.Count){throw 'Missing route cameras'}
 $result[$condition]=@{cameras=$rows.Count;route_cameras=$driving.Count;
  max_all_tris_percent=($rows.tris_percent|Measure-Object -Maximum).Maximum;
  max_route_tris_percent=($driving.tris_percent|Measure-Object -Maximum).Maximum;
  max_world_draw_delta=($rows.world_draw_delta|Measure-Object -Maximum).Maximum;
  max_instance_draw_delta=($rows.instance_draw_delta|Measure-Object -Maximum).Maximum}
 $checked+=$rows.Count
}
$report=@{source='native exact-stats.json, metadata only; no image decode';conditions=$result;checked=$checked;
 pose_projection_equal=$true;native_mesh_counts_match_glb=$true;violations=$bad;pass=(!$bad.Count)}
$report|ConvertTo-Json -Depth 7|Set-Content "artifacts/life-r4/$Tag-metadata-budget.json"
$report|ConvertTo-Json -Depth 7|Write-Output
if(!$report.pass){throw 'Candidate exceeds unchanged route/draw budget'}
