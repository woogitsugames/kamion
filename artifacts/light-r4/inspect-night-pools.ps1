$ErrorActionPreference='Stop'
$rows=@()
foreach($tier in @('Low','High')){
    $proof=Get-Content "$PSScriptRoot/baseline/$tier-night/lamp-probes.json" -Raw|ConvertFrom-Json
    foreach($camera in $proof.cameras){
        if($camera.poolGroundPoints.Count -ne $camera.pools -or $camera.poolGroundViewport.Count -ne $camera.pools){throw 'Incomplete ground-pool evidence'}
        $pools=@()
        for($i=0;$i -lt $camera.pools;$i++){
            $g=$camera.poolGroundPoints[$i];$v=$camera.poolGroundViewport[$i];$h=$camera.headsAndWeights[$i]
            $visible=$g.w -gt .5 -and $v.z -gt 0 -and $v.x -ge 0 -and $v.x -le 1 -and $v.y -ge 0 -and $v.y -le 1 -and $h.w -gt .1
            $pools+=@{head=$h;ground=$g;viewport=$v;geometrically_in_view=$visible;head_above_ground_m=($h.y-$g.y);ground_relative_camera_m=($g.y-$camera.position.y);nominal_lux_no_occlusion=$camera.nominalRoadLuxNoOcclusion[$i]}
        }
        $rows+=@{tier=$tier;camera=$camera.camera;pool_count=$camera.pools;ground_points_in_view=@($pools|Where-Object geometrically_in_view).Count;
            pools=$pools;lamp_surfaces=$camera.lampSurfaces;exposure=$camera.exposure;pool_colour=$camera.exposedPoolColor}
    }
}
@{scope='Geometric source/raycast/view evidence only. In-view points can still be occluded; nominal lux omit occlusion and calibration. Not a visibility or lighting-quality verdict.';cameras=$rows}|ConvertTo-Json -Depth 10|Set-Content "$PSScriptRoot/night-pool-evidence.json" -Encoding utf8
$rows|Where-Object camera -In @('driver-andersa-to-putry','route-putry-approach','g3b-rondo-putry-approach','stretch-05-docks','truck-34')|
    Select-Object tier,camera,pool_count,ground_points_in_view|Format-Table -AutoSize
