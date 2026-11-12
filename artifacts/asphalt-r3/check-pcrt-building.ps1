$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
# Tiny metadata check of one source footprint, not a world/mesh/image analysis.
$buildingPath='Data/Regions/bialystok-industrial-c/buildings.geojson'
$photoPath='artifacts/asphalt-r2/backlog-r3-references/pcrt-coordinate-precheck.json'
$source=Get-Content $buildingPath -Raw|ConvertFrom-Json
if($source.crs.properties.name -ne 'urn:ogc:def:crs:EPSG::2180'){throw 'Unexpected CRS'}
$id='bdot:2BE4B431-C92B-1BF0-E053-CC2BA8C0D140'
$features=@($source.features|Where-Object {$_.properties.id -eq $id})
if($features.Count -ne 1 -or $features[0].geometry.type -ne 'MultiPolygon'){throw 'Unexpected footprint'}
function Inside-Ring([object[]]$Ring,[double]$X,[double]$Y){
 $inside=$false
 $j=$Ring.Count-1
 for($i=0;$i -lt $Ring.Count;$i++){
  $a=$Ring[$i];$b=$Ring[$j]
  if(($a[1] -gt $Y) -ne ($b[1] -gt $Y)){
   $cut=($b[0]-$a[0])*($Y-$a[1])/($b[1]-$a[1])+$a[0]
   if($X -lt $cut){$inside=-not $inside}
  }
  $j=$i
 }
 return $inside
}
$rows=@()
foreach($photo in @(Get-Content $photoPath -Raw|ConvertFrom-Json)){
 if(-not $photo.epsg2180){$rows+=@{title=$photo.title;has_point=$false;inside=$null};continue}
 $inside=$false
 foreach($poly in $features[0].geometry.coordinates){
  $part=Inside-Ring $poly[0] $photo.epsg2180[0] $photo.epsg2180[1]
  for($hole=1;$hole -lt $poly.Count;$hole++){if(Inside-Ring $poly[$hole] $photo.epsg2180[0] $photo.epsg2180[1]){$part=$false}}
  $inside=$inside -or $part
 }
 $rows+=@{title=$photo.title;has_point=$true;inside=$inside;epsg2180=$photo.epsg2180;local_en=$photo.local_en}
}
[ordered]@{read_at=(Get-Date -Format o);building_source=$buildingPath;building_source_sha256=(Get-FileHash $buildingPath).Hash;building_id=$id;properties=$features[0].properties;photo_points_source=$photoPath;photo_points_sha256=(Get-FileHash $photoPath).Hash;rows=$rows;method='Even-odd ray crossing on all MultiPolygon outer rings minus holes, double precision EPSG2180.';note='Containment of declared approximate metadata points only. GPS accuracy and a fitted camera pose are not established. Photo3 has no point; this does not identify its ground material or authorize model edits.'}|ConvertTo-Json -Depth 10|Set-Content artifacts/asphalt-r3/reference/PCRT-BUILDING-CHECK.json
$rows|Select-Object title,has_point,inside|Format-Table -AutoSize
