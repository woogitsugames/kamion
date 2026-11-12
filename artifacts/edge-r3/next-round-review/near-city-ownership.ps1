$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$source='Data/Regions/bialystok-industrial-c/buildings.geojson'
$data=Get-Content $source -Raw|ConvertFrom-Json
$cache=Get-Content Data/raw/derived/bialystok-industrial-c/world/far_field_gis_cache.json -Raw|ConvertFrom-Json
$proofPath='artifacts/edge-r3/proof-cameras.json'
$proof=Get-Content $proofPath -Raw|ConvertFrom-Json
$ids=@('sbs-g3-a-303305168125936','sbs-g3-a-320215796381417','sbs-g3-a-454716650857984')
$rows=foreach($camera in $proof.cameras|Where-Object id -in $ids){
    $fe=$camera.look_at[0]-$camera.pos[0];$fn=$camera.look_at[1]-$camera.pos[1]
    $length=[Math]::Sqrt($fe*$fe+$fn*$fn);$fe/=$length;$fn/=$length
    $halfFov=[Math]::Atan([Math]::Tan($camera.fov_deg*[Math]::PI/360)*16/9)
    foreach($b in $data.features|Where-Object {$_.properties.function -eq 'budynek wielorodzinny' -and $_.properties.height_m -ge 25}){
        $ring=if($b.geometry.type -eq 'MultiPolygon'){$b.geometry.coordinates[0][0]}else{$b.geometry.coordinates[0]}
        $e=($ring|ForEach-Object {$_[0]}|Measure-Object -Average).Average-$cache.origin_epsg2180[0]
        $n=($ring|ForEach-Object {$_[1]}|Measure-Object -Average).Average-$cache.origin_epsg2180[1]
        if([Math]::Abs($e) -gt 1024 -or [Math]::Abs($n) -gt 1024){continue}
        $ve=$e-$camera.pos[0];$vn=$n-$camera.pos[1]
        $forward=$ve*$fe+$vn*$fn;$right=$ve*$fn-$vn*$fe
        $angle=[Math]::Atan2($right,$forward)
        if($forward -le 0 -or [Math]::Abs($angle) -gt $halfFov){continue}
        [PSCustomObject]@{camera=$camera.id;building_id=$b.properties.id;e=$e;n=$n;
            position_method='arithmetic mean of vertices of first outer polygon, diagnostic only';
            height_m=$b.properties.height_m;height_source=$b.properties.height_source;
            ground_z_evrf2007=$b.properties.ground_z_evrf2007;
            forward_distance_m=$forward;horizontal_angle_deg=$angle*180/[Math]::PI;
            centroid_inside_low_far=($forward -le 900);inside_region=$true;
            ownership='region buildings, not far_field';occlusion='UNVERIFIED';photo_identity='UNVERIFIED'}
    }
}
@{source_sha256=(Get-FileHash $source -Algorithm SHA256).Hash;
  cameras_sha256=(Get-FileHash $proofPath -Algorithm SHA256).Hash;
  note='Read-only ownership diagnosis: source regional apartment buildings already exist inside the tile. No claim of an actual missing mesh, wrong height, visibility or photographic identity. Do not duplicate them in far-field or paint them over nearer vegetation.';
  candidates=@($rows)}|ConvertTo-Json -Depth 7|Set-Content "$PSScriptRoot/near-city-ownership.json"
$rows|Group-Object camera|Select-Object Name,Count|Format-Table -AutoSize
