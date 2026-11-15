param([string]$Tag = 'probe-before')
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dusk-cal-0199'
$a = "$wt\artifacts\dusk-cal-0199"; $st = "$a\$Tag.status"
Set-Location $wt; . scripts/env.ps1
"start $(Get-Date -f HH:mm:ss)" | Set-Content $st
while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Owner dusk-cal-0199
try {
  $log = "$a\$Tag.log"
  Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod', 'Game.Rendering.Editor.TwilightSkyProbe.Dump', '-probeOut', "$a\$Tag.tsv") | Out-Null
  Select-String -Path $log -Pattern 'error CS\d+|TwilightSkyProbe' | Select-Object -First 8 | ForEach-Object { $_.Line } | Add-Content $st
} finally {
  pwsh scripts/unity-slot.ps1 -Release -Owner dusk-cal-0199
  git -C $wt checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings 2>$null
  "done $(Get-Date -f HH:mm:ss)" | Add-Content $st
}
