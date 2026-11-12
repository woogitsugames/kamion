# Read-only prediction of the source panorama's zero-opacity lower hemisphere.
# Does not assert that it causes the observed wedge; compare with geometry masks.
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$presetPath='game/Assets/_Project/Rendering/Settings/Lighting/LP_Clear.asset'
$sourcePath='game/Assets/_Project/Rendering/Resources/Sky/ClearCloudsSource.json'
$preset=Get-Content $presetPath -Raw
if($preset -notmatch 'sunElevationDeg: ([\d.]+)'){throw 'Sun elevation missing'};$elevation=[double]$Matches[1]
if($preset -notmatch 'sunAzimuthDeg: ([\d.]+)'){throw 'Sun azimuth missing'};$azimuth=[double]$Matches[1]
$source=Get-Content $sourcePath -Raw|ConvertFrom-Json
$sv=$source.sunDirection;$sl=[Math]::Sqrt($sv.x*$sv.x+$sv.y*$sv.y+$sv.z*$sv.z)
$sourceElevation=[Math]::Asin($sv.y/$sl)*180/[Math]::PI
$delta=($sourceElevation-$elevation)*[Math]::PI/180
$az=$azimuth*[Math]::PI/180
# SourceRotation aligns azimuth, then elevation: R^-1 * Up in world space.
$nx=[Math]::Sin($az)*[Math]::Sin($delta);$ny=[Math]::Cos($delta);$nz=[Math]::Cos($az)*[Math]::Sin($delta)
$proof=Get-Content "$PSScriptRoot/proof-cameras.json" -Raw|ConvertFrom-Json
$ids=@('sbs-g3-a-2948595898752384','sbs-g3-a-303305168125936')
$rows=foreach($c in $proof.cameras|Where-Object id -in $ids){
    $fx=$c.look_at[0]-$c.pos[0];$fz=$c.look_at[1]-$c.pos[1];$fy=$c.look_at[2]-$c.pos[2]
    $fl=[Math]::Sqrt($fx*$fx+$fy*$fy+$fz*$fz);$fx/=$fl;$fy/=$fl;$fz/=$fl
    $rl=[Math]::Sqrt($fx*$fx+$fz*$fz);$rx=$fz/$rl;$rz=-$fx/$rl
    $ux=$fy*$rz;$uy=$fz*$rx-$fx*$rz;$uz=-$fy*$rx
    $nf=$nx*$fx+$ny*$fy+$nz*$fz;$nr=$nx*$rx+$nz*$rz;$nu=$nx*$ux+$ny*$uy+$nz*$uz
    $tanV=[Math]::Tan($c.fov_deg*[Math]::PI/360);$tanH=$tanV*1280/720
    $points=foreach($x in @(0,640,1279)){
        $sx=2*$x/1280-1;$sy=-($nf+$nr*$sx*$tanH)/($nu*$tanV)
        @{x=$x;y=(1-$sy)*720/2}
    }
    @{camera=$c.id;width=1280;height=720;source_horizon_line=$points;
      world_horizon_center_y=(1+$fy/($uy*$tanV))*720/2}
}
@{hypothesis_only=$true;source_sun_elevation_deg=$sourceElevation;clear_sun_elevation_deg=$elevation;
  clear_sun_azimuth_deg=$azimuth;tilt_deg=$sourceElevation-$elevation;
  transformed_source_horizon_normal=@($nx,$ny,$nz);cameras=@($rows);
  sources=@{preset=$presetPath;preset_sha256=(Get-FileHash $presetPath -Algorithm SHA256).Hash;
    cloud_metadata=$sourcePath;cloud_metadata_sha256=(Get-FileHash $sourcePath -Algorithm SHA256).Hash};
  note='Predicted source opacity cutoff only, from the current SourceRotation rule. World-horizon fade, cloud content, fog and tone mapping also affect the image. Not a cause determination or a photo-pose calibration.'}|
    ConvertTo-Json -Depth 7|Set-Content "$PSScriptRoot/cloud-horizon-prediction.json"
$rows|ConvertTo-Json -Depth 5
