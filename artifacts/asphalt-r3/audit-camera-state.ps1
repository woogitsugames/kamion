param([ValidatePattern('^candidate[0-9]*$')][string]$After='candidate')
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$plan=Get-Content "$PSScriptRoot/capture-plan.json" -Raw|ConvertFrom-Json
$expected=@($plan.expected_ids)
if(-not $expected.Count -or @($expected|Select-Object -Unique).Count -ne $expected.Count){throw 'Invalid camera plan'}
$expectPath="$PSScriptRoot/material-expectations-$After.json"
$expect=Get-Content $expectPath -Raw|ConvertFrom-Json -AsHashtable
$changes=$expect.ground_changes
if($null -eq $changes){throw 'Explicit ground_changes declaration required, even if empty'}
$rootChanges=if($expect.ContainsKey('root_changes')){$expect.root_changes}else{@{}}
$groundIds=@('road_paving','yard_asphalt','yard_behaton','yard_paving','yard_concrete','yard_concrete_worn','yard_slabs','decal_yard_patch_light','decal_yard_patch_dark')
$rows=@();$poses=@();$materials=@()
function Json-Same($A,$B){return ($A|ConvertTo-Json -Compress -Depth 8) -eq ($B|ConvertTo-Json -Compress -Depth 8)}
function Expected-Value($Actual,$Value){
 if($Value -is [array] -and $Value.Count -eq 4){
  if($null -eq $Actual -or 'x' -notin $Actual.PSObject.Properties.Name){return $false}
  $v=@($Actual.x,$Actual.y,$Actual.z,$Actual.w)
  for($i=0;$i -lt 4;$i++){if([Math]::Abs([double]$v[$i]-[double]$Value[$i]) -gt .00001){return $false}}
  return $true
 }
 if($Value -is [double] -or $Value -is [long] -or $Value -is [int]){
  return $null -ne $Actual -and [Math]::Abs([double]$Actual-[double]$Value) -le .00001
 }
 return Json-Same $Actual $Value
}
function Png-Size([string]$Path){
 $stream=[IO.File]::OpenRead($Path)
 try{$header=[byte[]]::new(24);if($stream.Read($header,0,24) -ne 24){throw "Incomplete PNG: $Path"}}
 finally{$stream.Dispose()}
 if([BitConverter]::ToString($header,0,8) -ne '89-50-4E-47-0D-0A-1A-0A'){throw "Not a PNG: $Path"}
 return @([Net.IPAddress]::NetworkToHostOrder([BitConverter]::ToInt32($header,16)),[Net.IPAddress]::NetworkToHostOrder([BitConverter]::ToInt32($header,20)))
}
$poseFields=@('rootToWorld','view','projection','position','fov','aspect','width','height','anchorZ','originShift')
$rootMaterialFields=@('roadWear','roadExclusion','roadCrackStrength','roadDetailFade','roadCracksEnabled','roadPhotoEnabled','roadSealStrengthProperty','roadSealStrength','paintWear','freshPaintWear','kerbWear','pavingGrime','kerbExclusion','pavingExclusion','pavingGrimeBase','detailGlobal','paintUnderlay','maskFormat')
foreach($field in $rootChanges.Keys){if($field -notin $rootMaterialFields){throw "Unknown declared root field: $field"}}
foreach($series in 'Low-overcast','Low-clear','High-overcast','High-clear'){
 $beforeDir="$PSScriptRoot/baseline/$series";$afterDir="$PSScriptRoot/$After/$series"
 $snap=@(Get-ChildItem "$afterDir/runtime-cameras" -Filter '*.json')
 $png=@(Get-ChildItem $afterDir -Filter '*.png'|Where-Object BaseName -NotMatch '(_mask|_envcube)$')
 $pngIds=@($png|ForEach-Object BaseName)
 if($snap.Count -ne $expected.Count -or $png.Count -ne $expected.Count -or @(Compare-Object $expected $pngIds).Count){throw "Incomplete capture: $series"}
 $seen=@{};$sizes=@{}
 foreach($file in $snap){
  $a=Get-Content $file.FullName -Raw|ConvertFrom-Json
  $b=Get-Content "$beforeDir/runtime-cameras/$($file.Name)" -Raw|ConvertFrom-Json
  $id=$a.camera -replace '^QA_',''
  if($id -notin $expected -or $seen.ContainsKey($id)){throw "Unexpected/duplicate snapshot: $series/$id"}
  $seen[$id]=$true
  foreach($field in $poseFields){
   if($field -notin $a.PSObject.Properties.Name -or $field -notin $b.PSObject.Properties.Name -or -not(Json-Same $a.$field $b.$field)){$poses+="$series/${id}:$field"}
  }
  foreach($field in 'rootToWorld','view','projection'){if(@($a.$field).Count -ne 16 -or @($b.$field).Count -ne 16){$poses+="$series/${id}:$field length"}}
  if(-not(Json-Same (Png-Size "$beforeDir/$id.png") (Png-Size "$afterDir/$id.png"))){$poses+="$series/${id}:PNG dimensions"}
  $sizes["$($a.width)x$($a.height)"]=$true
  foreach($field in $rootMaterialFields){
   if($field -notin $a.PSObject.Properties.Name -or $field -notin $b.PSObject.Properties.Name){throw "Missing root material field: $field"}
   $ok=if($rootChanges.ContainsKey($field)){Expected-Value $a.$field $rootChanges[$field]}else{Json-Same $a.$field $b.$field}
   if(-not $ok){$materials+="$series/${id}:root $field"}
  }
  $beforeGround=@{};$afterGround=@{}
  foreach($record in @($b.grounds)){if($beforeGround.ContainsKey($record.id)){throw 'Duplicate baseline material'};$beforeGround[$record.id]=$record}
  foreach($record in @($a.grounds)){if($afterGround.ContainsKey($record.id)){throw 'Duplicate candidate material'};$afterGround[$record.id]=$record}
  if(@(Compare-Object $groundIds @($beforeGround.Keys)).Count -or @(Compare-Object $groundIds @($afterGround.Keys)).Count){throw 'Incomplete ground material snapshots'}
  foreach($groundId in $changes.Keys){if(-not $afterGround.ContainsKey($groundId) -or -not $afterGround[$groundId].exists -or -not $beforeGround[$groundId].exists){throw "Declared material absent: $groundId"}}
  foreach($groundId in $beforeGround.Keys){
   $beforeRecord=$beforeGround[$groundId];$afterRecord=$afterGround[$groundId]
   $declared=if($changes.ContainsKey($groundId)){$changes[$groundId]}else{@{}}
   foreach($field in $declared.Keys){if($field -notin $afterRecord.PSObject.Properties.Name){throw "Unknown declared field: $groundId/$field"}}
   foreach($field in $beforeRecord.PSObject.Properties.Name){
    $ok=if($declared.ContainsKey($field)){Expected-Value $afterRecord.$field $declared[$field]}else{Json-Same $afterRecord.$field $beforeRecord.$field}
    if(-not $ok){$materials+="$series/${id}:$groundId/$field"}
   }
  }
  if(-not(Json-Same $a.yardGrime $afterGround['yard_paving'].grime)){$materials+="$series/${id}:legacy yardGrime inconsistent"}
 }
 $rows+=[pscustomobject]@{series=$series;png=$png.Count;snapshots=$snap.Count;render_targets=@($sizes.Keys|Sort-Object)}
}
[ordered]@{after=$After;expected_camera_conditions=($expected.Count*4);rows=$rows;pose_matrix_differences=$poses;material_differences=$materials;expectations_sha256=(Get-FileHash $expectPath).Hash;note='Actual matrices, PNG sizes and material uniforms. Does not prove per-pixel ownership, visual quality or GPU timing.'}|ConvertTo-Json -Depth 6|Set-Content "$PSScriptRoot/camera-state-audit-$After.json"
if($poses.Count -or $materials.Count){throw 'Camera or material mismatch'}
"Verified $($expected.Count*4) matching camera conditions and explicitly declared material changes."
