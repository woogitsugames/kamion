# dusk-cal-0199 runner. pwsh run.ps1 -Tag <t> [-Import] [-Tests] [-Lightings dusk,night] [-Tiers Low,High] [-Cams ...] [-Rq ''] [-EnvDump]
param([string]$Tag = 'r1', [switch]$Import, [switch]$Tests, [switch]$NoRender, [string]$Lightings = 'dusk,night', [string]$Tiers = 'Low,High',
      [string]$Cams = 'chase,route_putry_approach,driver_andersa_to_putry,kwadrat_park_gate,trailer-34', [string]$Rq = '', [switch]$EnvDump)
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dusk-cal-0199'
$a = "$wt\artifacts\dusk-cal-0199"
$st = "$a\$Tag.status"
Set-Location $wt
. scripts/env.ps1
"start $(Get-Date -f HH:mm:ss)" | Set-Content $st
while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Owner dusk-cal-0199
"slot $(Get-Date -f HH:mm:ss)" | Add-Content $st
try {
  $log = "$a\apply-$Tag.log"
  $code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod', 'Game.Rendering.Editor.NightWindowAssets.ApplyRegionMaterials')
  if (Select-String -Path $log -Pattern 'error CS\d+' -Quiet) { "FAILED compile (see $log)" | Add-Content $st; Select-String -Path $log -Pattern 'error CS\d+' | Select-Object -First 8 | ForEach-Object { $_.Line } | Add-Content $st; throw "compile" }
  Select-String -Path $log -Pattern '\[NightWindows\]' | ForEach-Object { $_.Line } | Add-Content $st
  if ($Tests) {
    pwsh scripts/test.ps1 -Platform EditMode *>&1 | Select-Object -Last 6 | Add-Content $st
  }
  if (-not $NoRender) {
    foreach ($t in ($Tiers -split ',')) { foreach ($l in ($Lightings -split ',')) {
      $args2 = @('-Scene', 'WorldC', '-Tier', $t, '-Lighting', $l, '-Cameras', $Cams, '-OutputDir', "$a/$Tag/$t-$l", '-TimeFrames', '0')
      if ($Rq) { $args2 += @('-Rq', $Rq) }
      if ($EnvDump) { $args2 += '-EnvDump' }
      pwsh scripts/visual-qa.ps1 @args2 *>&1 | Select-Object -Last 2 | Add-Content $st
      $ql = Get-ChildItem "$wt\artifacts\logs\visual-qa-WorldC-*.log" | Sort-Object LastWriteTime | Select-Object -Last 1
      Select-String -Path $ql.FullName -Pattern '^\[QA\] (street lamps|lamp pools)|^\[VISUALQA\] .*(draws|tris)|SceneStats|VISUALQA_RESULT' | ForEach-Object { $_.Line } | Set-Content "$a/$Tag/$t-$l/qa-lines.txt"
    } }
  }
} finally {
  pwsh scripts/unity-slot.ps1 -Release -Owner dusk-cal-0199
  git -C $wt checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting/LP_Dusk.asset game/Assets/_Project/Rendering/Settings/Lighting/LP_Night.asset 2>$null
  "done $(Get-Date -f HH:mm:ss)" | Add-Content $st
}
