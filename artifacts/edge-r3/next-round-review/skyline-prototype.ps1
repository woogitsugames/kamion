# Geometry feasibility study only. No game asset, shader, camera or source changes.
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$cachePath='Data/raw/derived/bialystok-industrial-c/world/far_field_gis_cache.json'
$profilePath='artifacts/edge-r3/before-source/far_field_apron.json'
$cache=Get-Content $cachePath -Raw|ConvertFrom-Json
$profile=Get-Content $profilePath -Raw|ConvertFrom-Json
$border=$profile.border_z
$half=[double]$profile.half_m
$ring=@();foreach($side in @('south','east','north','west')){$ring+=@($border.$side)[0..127]}
if($ring.Count -ne 512){throw 'Expected 16 m profile with 512 unique samples'}
$mean=($ring|Measure-Object -Average).Average
$smooth=for($i=0;$i -lt 512;$i++){$sum=0.0;for($j=-6;$j -le 6;$j++){$sum+=$ring[($i+$j+512)%512]};$sum/13}
function Ground([double]$e,[double]$n){
    $eb=[Math]::Clamp($e,-$half,$half);$nb=[Math]::Clamp($n,-$half,$half)
    $ds=[Math]::Abs($nb+$half);$de=[Math]::Abs($eb-$half);$dn=[Math]::Abs($nb-$half);$dw=[Math]::Abs($eb+$half)
    $min=[Math]::Min([Math]::Min($ds,$de),[Math]::Min($dn,$dw))
    if($min -eq $ds){$side='south';$offset=0;$t=($eb+$half)/(2*$half)}
    elseif($min -eq $de){$side='east';$offset=128;$t=($nb+$half)/(2*$half)}
    elseif($min -eq $dn){$side='north';$offset=256;$t=($half-$eb)/(2*$half)}
    else{$side='west';$offset=384;$t=($half-$nb)/(2*$half)}
    $x=[Math]::Clamp($t,0,1)*128;$i=[Math]::Min([int][Math]::Floor($x),127);$f=$x-$i
    $z0=$border.$side[$i]*(1-$f)+$border.$side[$i+1]*$f
    $zs=$smooth[($offset+$i)%512]*(1-$f)+$smooth[($offset+$i+1)%512]*$f
    $d=[Math]::Sqrt(($e-$eb)*($e-$eb)+($n-$nb)*($n-$nb))
    $t1=[Math]::Clamp($d/220,0,1);$s1=$t1*$t1*(3-2*$t1)
    $t2=[Math]::Clamp(($d-220)/1400,0,1);$s2=$t2*$t2*(3-2*$t2)
    $near=$z0+($zs-0.15-$z0)*$s1;$far=$zs-0.25+0.08*($mean-$zs)
    return $near+($far-$near)*$s2
}
$proof=Get-Content artifacts/edge-r3/proof-cameras.json -Raw|ConvertFrom-Json
$targetIds=@('sbs-g3-a-303305168125936','sbs-g3-a-320215796381417','sbs-g3-a-454716650857984')
$targets=@($proof.cameras|Where-Object id -in $targetIds)
$ranked=foreach($b in $cache.buildings|Where-Object {$_.typ -eq 'block' -and $_.h -ge 20 -and $_.height_source -eq 'gugik-lod1-measuredHeight'}){
    $e=($b.rect|ForEach-Object {$_[0]}|Measure-Object -Average).Average
    $n=($b.rect|ForEach-Object {$_[1]}|Measure-Object -Average).Average
    $score=0.0
    foreach($c in $targets){
        $fe=$c.look_at[0]-$c.pos[0];$fn=$c.look_at[1]-$c.pos[1];$length=[Math]::Sqrt($fe*$fe+$fn*$fn);$fe/=$length;$fn/=$length
        $ve=$e-$c.pos[0];$vn=$n-$c.pos[1];$forward=$ve*$fe+$vn*$fn;$right=$ve*$fn-$vn*$fe
        $halfFov=[Math]::Atan([Math]::Tan($c.fov_deg*[Math]::PI/360)*16/9)
        if($forward -gt 0 -and [Math]::Abs([Math]::Atan2($right,$forward)) -le $halfFov){$score=[Math]::Max($score,$b.h/$forward)}
    }
    if($score -gt 0){[PSCustomObject]@{building=$b;score=$score;id=$b.id}}
}
$selected=@($ranked|Sort-Object @{e='score';Descending=$true},id|Select-Object -First 64|ForEach-Object building)
$blocks=foreach($b in $selected){
    $e=($b.rect|ForEach-Object {$_[0]}|Measure-Object -Average).Average
    $n=($b.rect|ForEach-Object {$_[1]}|Measure-Object -Average).Average
    @{id=$b.id;rect=$b.rect;height_m=$b.h;height_source=$b.height_source;
      ground_m=(Ground $e $n);ground_source='WORKING_VALUE extrapolated border profile';
      source_storeys=$b.storeys;centroid=@($e,$n)}
}
@{prototype_only=$true;shipping_asset=$false;limit=64;limit_status='WORKING_VALUE';
  selection='block h>=20m, measuredHeight only, true source centroid within horizontal FOV of the three flagged G3-A views; descending maximum h/forward distance, ID tie-break; cap64';
  selection_camera_ids=$targetIds;selection_candidate_count=@($ranked).Count;
  source_sha256=(Get-FileHash $cachePath -Algorithm SHA256).Hash;
  profile_sha256=(Get-FileHash $profilePath -Algorithm SHA256).Hash;
  count=@($blocks).Count;box_triangles=12*@($blocks).Count;
  box_triangles_status='analytical count for hypothetical boxes, not a measured Unity mesh';blocks=@($blocks)}|
    ConvertTo-Json -Depth 8|Set-Content "$PSScriptRoot/skyline-prototype.json"

$cam=$proof.cameras|Where-Object id -eq 'sbs-g3-a-303305168125936'
$ce=$cam.pos[0];$cn=$cam.pos[1];$cy=$cam.pos[2]
$fx=$cam.look_at[0]-$ce;$fz=$cam.look_at[1]-$cn;$fy=$cam.look_at[2]-$cy
$len=[Math]::Sqrt($fx*$fx+$fy*$fy+$fz*$fz);$fx/=$len;$fy/=$len;$fz/=$len
$rl=[Math]::Sqrt($fx*$fx+$fz*$fz);$rx=$fz/$rl;$rz=-$fx/$rl
$ux=$fy*$rz;$uy=$fz*$rx-$fx*$rz;$uz=-$fy*$rx
$scale=540/(2*[Math]::Tan($cam.fov_deg*[Math]::PI/360))
function Num([double]$v){$v.ToString('0.###',[Globalization.CultureInfo]::InvariantCulture)}
function Project([double]$e,[double]$n,[double]$y){
    $x=$e-$ce;$z=$n-$cn;$h=$y-$cy;$depth=$x*$fx+$h*$fy+$z*$fz
    if($depth -le 1){return $null}
    return "$(Num (480+($x*$rx+$z*$rz)/$depth*$scale)),$(Num (270-($x*$ux+$h*$uy+$z*$uz)/$depth*$scale))"
}
$svg=[Collections.Generic.List[string]]::new()
$svg.Add('<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540"><rect width="960" height="540" fill="#fafafa"/>')
foreach($b in $blocks){
    $top=@($b.rect|ForEach-Object {Project $_[0] $_[1] ($b.ground_m+$b.height_m)})
    $bottom=@($b.rect|ForEach-Object {Project $_[0] $_[1] $b.ground_m})
    if($top.Count -ne 4 -or $bottom.Count -ne 4){continue}
    $svg.Add("<polygon points='$($top -join ' ')' fill='none' stroke='#815020' stroke-width='0.8'/>")
    for($i=0;$i -lt 4;$i++){$j=($i+1)%4;$pts="$($top[$i]) $($top[$j]) $($bottom[$j]) $($bottom[$i])";$svg.Add("<polygon points='$pts' fill='none' stroke='#815020' stroke-width='0.6'/>")}
}
$svg.Add("<g font-family='Arial' fill='#222'><text x='16' y='27' font-size='18'>Studium geometrii GIS — $(@($blocks).Count) brył 1:1, nie render gry</text><text x='16' y='49' font-size='13'>Kamera 303305 / poza B; bez far clip, okluzji i mgły; wysokość podstawy WORKING_VALUE</text><text x='16' y='520' font-size='12'>Selekcja wg znaczenia kątowego w 3 wskazanych kadrach; bez oceny podobieństwa fotograficznego.</text></g></svg>")
[IO.File]::WriteAllLines("$PSScriptRoot/skyline-prototype.svg",$svg,[Text.UTF8Encoding]::new($false))
& magick -limit thread 1 "$PSScriptRoot/skyline-prototype.svg" "$PSScriptRoot/skyline-prototype.png"
if($LASTEXITCODE -ne 0){throw 'Prototype rasterization failed'}
"Prototype count=$(@($blocks).Count), triangles=$(12*@($blocks).Count)"
