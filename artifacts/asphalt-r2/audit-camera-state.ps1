param([ValidatePattern('^candidate[0-9]*$')][string]$After='candidate2')
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$rows=@();$differences=@();$scopeErrors=@()
function Same-Vector($Actual,[double[]]$Expected){
 if($null -eq $Actual){return $false}
 $values=@($Actual.x,$Actual.y,$Actual.z,$Actual.w)
 for($i=0;$i -lt 4;$i++){if([Math]::Abs([double]$values[$i]-$Expected[$i]) -gt 0.00001){return $false}}
 return $true
}
foreach($series in 'Low-overcast','Low-clear','High-overcast','High-clear'){
 $sizes=@{}
 $snap=@(Get-ChildItem "artifacts/asphalt-r2/$After/$series/runtime-cameras" -Filter '*.json')
 $png=@(Get-ChildItem "artifacts/asphalt-r2/$After/$series" -Filter '*.png')
 if($snap.Count -ne 82 -or $png.Count -ne 82){throw "Incomplete capture: $series"}
 foreach($p in $snap){
  $a=Get-Content $p.FullName -Raw | ConvertFrom-Json
  $b=Get-Content "artifacts/asphalt-r2/baseline/$series/runtime-cameras/$($p.Name)" -Raw | ConvertFrom-Json
  foreach($field in 'rootToWorld','view','projection','position','fov','aspect','width','height'){
   if(($a.$field | ConvertTo-Json -Compress) -ne ($b.$field | ConvertTo-Json -Compress)){$differences+="$series/$($p.Name):$field"}
  }
  $sizes["$($a.width)x$($a.height)"]=$true
  if($a.rootToWorld.Count -ne 16){$differences+="$series/$($p.Name):root length"}
  foreach($field in 'kerbExclusion','pavingExclusion'){
   if(-not (Same-Vector $a.$field @(400,-700,850,-250))){$scopeErrors+="$series/$($p.Name):$field"}
  }
  foreach($field in 'pavingGrimeBase','yardGrime'){
   if(-not (Same-Vector $a.$field @(0.42,0.62,0.45,0.5))){$scopeErrors+="$series/$($p.Name):$field"}
  }
  if(-not (Same-Vector $a.pavingGrime @(0.18,0.65,0.45,0.15))){$scopeErrors+="$series/$($p.Name):pavingGrime"}
  if(-not (Same-Vector $a.kerbWear @(0.35,0.16,0.55,1))){$scopeErrors+="$series/$($p.Name):kerbWear"}
 }
 $rows += [pscustomobject]@{series=$series;png=$png.Count;snapshots=$snap.Count;render_targets=@($sizes.Keys | Sort-Object)}
}
[ordered]@{after=$After;rows=$rows;pose_matrix_differences=$differences;scope_errors=$scopeErrors;note='Actual material uniforms and camera matrices, not proof of per-pixel scope or GPU performance.'} | ConvertTo-Json -Depth 5 | Set-Content "artifacts/asphalt-r2/camera-state-audit-$After.json"
if($differences.Count -or $scopeErrors.Count){throw 'Camera/material state mismatch'}
Write-Output '328 camera poses and material ownership uniforms verified.'
