# pwsh cab.ps1 -Tag base  (inside a -Unity step)
param([string]$Tag, [string]$Runs = 'High:clear;High:night;High:dusk;Low:night;Low:clear;Ultra:clear', [string]$Cameras = 'cab-driver,cab-dash,cab-hub')
$bad = 0
foreach ($r in $Runs.Split(';')) { $p = $r.Split(':')
  $out = "artifacts/night-truck-s24/$Tag/cab-$($p[0])-$($p[1])"
  $a = @('-Scene','DrivingLab','-Tier',$p[0],'-Lighting',$p[1],'-Width','1920','-Height','1080','-BuildTarget','Win64','-Cameras',$Cameras,'-OutputDir',$out)
  if ($p[0] -ne 'Low') { $a += '-Pc' }
  pwsh scripts/visual-qa.ps1 @a; if ($LASTEXITCODE) { $bad++ }
  git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings game/Packages 2>$null
}
exit $bad
