# pwsh ab.ps1 -Tag after2  (inside a -Unity step): spill A/B, GPU timing of the cab soft shadow and the lamp halo
param([string]$Tag)
$bad = 0
function QA([string]$out, [string[]]$extra) {
  $a = @('-Scene','DrivingLab','-Width','1920','-Height','1080','-BuildTarget','Win64','-OutputDir',"artifacts/night-truck-s24/$Tag/$out") + $extra
  pwsh scripts/visual-qa.ps1 @a; if ($LASTEXITCODE) { $script:bad++ }
  git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings game/Packages 2>$null
}
QA 'ab-nospill-High-night' @('-Tier','High','-Pc','-Lighting','night','-Cameras','cab-driver,cab-dash','-Rq','rq_cabspill=0')
foreach ($soft in 0,1) { QA "time-cabsoft$soft-High-clear" @('-Tier','High','-Pc','-Lighting','clear','-Cameras','cab-driver,cab-dash','-TimeFrames','60','-Rq',"rq_cabsoft=$soft") }
foreach ($soft in 0,1) { QA "time-cabsoft$soft-Ultra-clear" @('-Tier','Ultra','-Pc','-Lighting','clear','-Cameras','cab-driver','-TimeFrames','60','-Rq',"rq_cabsoft=$soft") }
QA 'time-lamps-High-night-brake' @('-Tier','High','-Pc','-Lighting','night','-TruckLamps','low,brake','-Cameras','plate-trailer,lamp-truck','-TimeFrames','60')
exit $bad
