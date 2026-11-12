# Read-only planar visibility diagnosis. Not an occlusion or photographic match test.
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$cachePath = 'Data/raw/derived/bialystok-industrial-c/world/far_field_gis_cache.json'
$cache = Get-Content $cachePath -Raw | ConvertFrom-Json
$cameraFile = Get-Content artifacts/edge-r3/proof-cameras.json -Raw | ConvertFrom-Json
$ids = @('sbs-g3-a-303305168125936','sbs-g3-a-320215796381417','sbs-g3-a-454716650857984')
$all = foreach ($camera in $cameraFile.cameras | Where-Object id -in $ids) {
    # Gate3 stores local [E,N,Y], not Unity [X,Y,Z].
    $ce = [double]$camera.pos[0]; $cn = [double]$camera.pos[1]
    $de = [double]$camera.look_at[0] - $ce; $dn = [double]$camera.look_at[1] - $cn
    $len = [Math]::Sqrt($de*$de+$dn*$dn); $fe=$de/$len; $fn=$dn/$len
    $objects = foreach ($building in $cache.buildings | Where-Object { $_.typ -eq 'block' -and $_.h -ge 20 }) {
        $e=0.0; $n=0.0
        foreach ($p in $building.rect) { $e += $p[0]; $n += $p[1] }
        $e /= $building.rect.Count; $n /= $building.rect.Count
        $be=[Math]::Min([Math]::Max($e,-1024),1024); $bn=[Math]::Min([Math]::Max($n,-1024),1024)
        $oe=$e-$be; $on=$n-$bn; $d=[Math]::Sqrt($oe*$oe+$on*$on)
        if ($d -le 0) { continue }
        $eff=if($d -le 140){$d}else{140+520*(1-[Math]::Exp(-($d-140)/950))}
        $ee=$be+$oe*$eff/$d; $en=$bn+$on*$eff/$d
        $viewE=$ee-$ce; $viewN=$en-$cn
        $forward=$viewE*$fe+$viewN*$fn
        $right=$viewE*$fn-$viewN*$fe
        $angle=[Math]::Atan2($right,$forward)*180/[Math]::PI
        # Include the whole horizontal FOV (vertical fov expanded by 16:9), plus 2 degrees for footprint.
        $halfFov=[Math]::Atan([Math]::Tan([double]$camera.fov_deg*[Math]::PI/360)*16/9)*180/[Math]::PI
        if ($forward -le 0 -or [Math]::Abs($angle) -gt ($halfFov+2)) { continue }
        @{id=$building.id;source=$building.height_source;height_m=$building.h;
          raw_e=$e;raw_n=$n;effective_e=$ee;effective_n=$en;
          horizontal_angle_deg=$angle;forward_distance_m=$forward;
          low_far_900m_excludes_centroid=($forward -gt 900)}
    }
    @{camera=$camera.id;camera_e=$ce;camera_n=$cn;candidate_blocks=@($objects|Sort-Object horizontal_angle_deg);
      in_horizontal_fov=@($objects).Count;beyond_low_far_centroids=@($objects|Where-Object low_far_900m_excludes_centroid).Count}
}
@{schema='edge-planar-visibility-diagnostic/1';source_sha256=(Get-FileHash $cachePath -Algorithm SHA256).Hash;
  note='Planar centroids only; no occlusion, vertical frustum, roof, fog, camera-pose verification or photographic identity claim. Current source foreshortening reproduced analytically. 900 m is the current Low far clip.';
  cameras=@($all)} | ConvertTo-Json -Depth 8 | Set-Content "$PSScriptRoot/skyline-visibility.json"
$all | Select-Object camera,in_horizontal_fov,beyond_low_far_centroids | Format-Table -AutoSize
