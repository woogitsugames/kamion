# pwsh time.ps1 -Tag after3 (inside -Unity step): repeated A/B timing, soft cab shadow and instrument spill, alternating order
param([string]$Tag)
function QA([string]$out, [string[]]$extra) {
  $a = @('-Scene','DrivingLab','-Width','1920','-Height','1080','-BuildTarget','Win64','-OutputDir',"artifacts/night-truck-s24/$Tag/$out") + $extra
  pwsh scripts/visual-qa.ps1 @a
  git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings game/Packages 2>$null
}
foreach ($rep in 1,2) { foreach ($soft in 1,0) { QA "time$rep-cabsoft$soft-High-clear" @('-Tier','High','-Pc','-Lighting','clear','-Cameras','cab-driver,cab-dash,cab-hub','-TimeFrames','120','-Rq',"rq_cabsoft=$soft") } }
foreach ($sp in 1,0) { QA "time-cabspill$sp-High-night" @('-Tier','High','-Pc','-Lighting','night','-Cameras','cab-driver,cab-dash','-TimeFrames','120','-Rq',"rq_cabspill=$sp") }
exit 0
