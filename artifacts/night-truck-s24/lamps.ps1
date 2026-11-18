# pwsh lamps.ps1 -Tag base  (inside a -Unity step)
param([string]$Tag, [string]$Runs = 'High:night:low;High:night:low,brake;High:dusk:low;Low:night:low;Low:night:low,brake')
$cams = 'lamp-trailer,lamp-truck,plate-trailer,plate-truck-bobtail'
$bad = 0
foreach ($r in $Runs.Split(';')) { $p = $r.Split(':')
  $out = "artifacts/night-truck-s24/$Tag/lamps-$($p[0])-$($p[1])-$($p[2].Replace(',','+'))"
  $a = @('-Scene','DrivingLab','-Tier',$p[0],'-Lighting',$p[1],'-TruckLamps',$p[2],'-Width','1920','-Height','1080','-BuildTarget','Win64','-Cameras',$cams,'-OutputDir',$out)
  if ($p[0] -ne 'Low') { $a += '-Pc' }
  pwsh scripts/visual-qa.ps1 @a; if ($LASTEXITCODE) { $bad++ }
  git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings game/Packages 2>$null
}
exit $bad
