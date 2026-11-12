$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((git branch --show-current).Trim() -ne 'gpt-life-r4'){throw 'Wrong branch'}
if(Test-Path artifacts/life-r4/before-inputs.json){throw 'Camera packet already frozen by capture'}
$packet=Get-Content artifacts/life-r4/cameras.json -Raw|ConvertFrom-Json
$wanted=@(Get-Content artifacts/life-r2/yard-targets-v2.json -Raw|ConvertFrom-Json)
$added=@()
function XY($item,[double]$x,[double]$y){
 $c=[math]::Cos($item.yaw);$s=[math]::Sin($item.yaw)
 return @(($item.e+$c*$x-$s*$y),($item.n+$s*$x+$c*$y))
}
foreach($item in $wanted){
 $side=@($packet.cameras|Where-Object id -eq "yard_$($item.p)_side8")
 if($side.Count -ne 1){throw 'Missing original yard pose'}
 $dx=$side[0].pos[0]-$item.e;$dy=$side[0].pos[1]-$item.n
 $sign=[math]::Sign([math]::Cos($item.yaw)*$dx+[math]::Sin($item.yaw)*$dy)
 if(!$sign){throw 'Unknown viewing side'}
 $trailer=$item.p.StartsWith('trailer_')
 $face=if($trailer){1.275-0.27+0.385/2}else{2.49/2-0.18+0.32/2}
 $axle=if($trailer){3.05}else{3.70-0.55}
 $height=if($trailer){0.535}else{0.51}
 $specs=@(@{name='wheel2';px=$sign*($face+2.2);py=$axle-0.65;pz=$height+0.20;tx=$sign*$face;ty=$axle;tz=$height;fov=40})
 if($trailer){$specs+=@{name='supports5';px=$sign*5.5;py=10.5;pz=1.0;tx=0;ty=11.525;tz=0.65;fov=50}}
 foreach($spec in $specs){
  $id="yard_$($item.p)_$($spec.name)"
  if($packet.cameras.id -contains $id){throw 'New camera already exists'}
  $pos=XY $item $spec.px $spec.py;$look=XY $item $spec.tx $spec.ty
  $camera=[ordered]@{id=$id;type='persp';kind='inspection';seat='yard';pos=@($pos[0],$pos[1],$item.z+$spec.pz);
   look_at=@($look[0],$look[1],$item.z+$spec.tz);fov_deg=$spec.fov;
   note="Actual historical target $($item.src), $($item.p); same viewing side as verified side8. Low view/occlusion UNVERIFIED until fresh render; target identity must match regenerated raw."}
  $added+=$camera
 }
}
$packet.cameras=@($packet.cameras)+$added
$packet|Add-Member -Force -NotePropertyName life_r4_note -NotePropertyValue 'Eight additive detail poses from actual yard targets: five outer wheel faces and three existing landing-leg locations. Old poses unchanged; raw identities and render visibility require validation.'
$packet|ConvertTo-Json -Depth 20|Set-Content artifacts/life-r4/cameras.json
@{added=$added;count=$added.Count;packet_count=$packet.cameras.Count;visibility='UNVERIFIED'}|ConvertTo-Json -Depth 10|Set-Content artifacts/life-r4/detail-camera-preflight.json
