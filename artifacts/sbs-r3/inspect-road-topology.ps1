$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Push-Location $root
try {
    function Project-Segment([double]$px,[double]$py,[double[]]$a,[double[]]$b) {
        $dx=$b[0]-$a[0];$dy=$b[1]-$a[1];$length2=$dx*$dx+$dy*$dy
        if($length2 -le 0){return $null}
        [double]$fraction=(($px-$a[0])*$dx+($py-$a[1])*$dy)/$length2
        # Branches avoid Math.Min overload selection rounding Decimal inputs to Int32.
        if($fraction -lt 0){$fraction=0.0}elseif($fraction -gt 1){$fraction=1.0}
        $qx=$a[0]+$fraction*$dx;$qy=$a[1]+$fraction*$dy
        [pscustomobject]@{fraction=$fraction;x=$qx;y=$qy;distance=[Math]::Sqrt(($px-$qx)*($px-$qx)+($py-$qy)*($py-$qy));heading=([Math]::Atan2($dx,$dy)*180/[Math]::PI+360)%360;signed_left=(($px-$qx)*(-$dy)+($py-$qy)*$dx)/[Math]::Sqrt($length2)}
    }
    $sanity=Project-Segment 2.5 3 @(0,0) @(10,0)
    if([Math]::Abs($sanity.fraction-0.25) -gt 1e-12 -or [Math]::Abs($sanity.distance-3) -gt 1e-12){throw 'Projection sanity failed'}
    $graphPath='Data/Regions/bialystok-industrial-c/roads.graph.json'
    $graph=Get-Content $graphPath -Raw | ConvertFrom-Json
    $origin=(Get-Content Data/Regions/bialystok-industrial-c/generated/world_manifest.json -Raw | ConvertFrom-Json).origin_epsg2180
    $cameraPath='Data/Regions/bialystok-industrial-c/sbs_cameras.json'
    $cameras=(Get-Content $cameraPath -Raw | ConvertFrom-Json).cameras
    $rows=@(foreach($sid in @('494288258686575','1801374876712141','3281350541967811','297817221966185')) {
        $camera=$cameras | Where-Object {$_.id -eq "sbs-g3-b-$sid"}
        [double]$px=[double]$camera.pos[0]+[double]$origin.x
        [double]$py=[double]$camera.pos[1]+[double]$origin.y
        $near=@(foreach($edge in $graph.edges) {
            $best=$null
            for($index=0;$index -lt ($edge.geometry.Count-1);$index++) {
                $projection=Project-Segment $px $py $edge.geometry[$index] $edge.geometry[$index+1]
                if($projection -and (!$best -or $projection.distance -lt $best.distance)){$best=$projection}
            }
            if($best){[pscustomobject]@{edge_id=$edge.id;osm_way=$edge.osm_way;name=$edge.attrs.name.v;highway=$edge.attrs.highway.v;lanes=$edge.attrs.lanes.v;oneway=$edge.attrs.oneway.v;bridge=$edge.attrs.bridge.v;distance_m=[Math]::Round($best.distance,4);segment_fraction=$best.fraction;segment_heading_grid_deg=[Math]::Round($best.heading,4);signed_left_of_segment_m=[Math]::Round($best.signed_left,4);nearest_local_en=@([Math]::Round($best.x-[double]$origin.x,4),[Math]::Round($best.y-[double]$origin.y,4))}}
        })
        [ordered]@{camera=$camera.id;stored_pos=$camera.pos;stored_view_grid_deg=([Math]::Atan2(($camera.look_at[0]-$camera.pos[0]),($camera.look_at[1]-$camera.pos[1]))*180/[Math]::PI+360)%360;nearest_edges=@($near | Sort-Object distance_m | Select-Object -First 6)}
    })
    [ordered]@{checked_at=(Get-Date -Format o);graph_sha256=(Get-FileHash $graphPath).Hash.ToLowerInvariant();camera_sha256=(Get-FileHash $cameraPath).Hash.ToLowerInvariant();projection_sanity=@{fraction=0.25;distance_m=3;passed=$true};note='Corrected projection: explicit double coordinates, branch clamp. Earlier Math.Min overload could round Decimal fraction to Int32 and choose endpoints. Graph only, no proof of generated road edge or camera approval.';cameras=$rows} | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $PSScriptRoot 'bridge-topology.json') -Encoding utf8
    foreach($row in $rows){$row.camera;$row.nearest_edges | Select-Object -First 3 edge_id,distance_m,segment_heading_grid_deg,bridge | Format-Table -AutoSize}
} finally {Pop-Location}
