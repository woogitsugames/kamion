$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dusk-cal-0199'
$st = "$wt\artifacts\dusk-cal-0199\basetest.status"
Set-Location $wt; . scripts/env.ps1
"start $(Get-Date -f HH:mm:ss)" | Set-Content $st
while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Owner dusk-cal-0199
try {
  git checkout -q --detach a08f9935d
  "base $(git rev-parse --short HEAD)" | Add-Content $st
  pwsh scripts/test.ps1 -Platform EditMode -Filter CarPaintMaterialTests *>&1 | Select-Object -Last 6 | Add-Content $st
} finally {
  git checkout -q dusk-cal-0199
  git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings 2>$null
  "back $(git rev-parse --short HEAD)" | Add-Content $st
  pwsh scripts/unity-slot.ps1 -Release -Owner dusk-cal-0199
  "done $(Get-Date -f HH:mm:ss)" | Add-Content $st
}
