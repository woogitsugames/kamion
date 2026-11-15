$d = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\spawn-fix-0262\artifacts\spawn-fix-0262'
Remove-Item "$d\green-all.done" -ErrorAction SilentlyContinue
pwsh -NoProfile -File "$d\run-editmode.ps1" -Tag green -Filter 'Game.Tests.StartClearanceTests;Game.Tests.RegionSelectTests'
pwsh -NoProfile -File "$d\run-editmode.ps1" -Tag playmode-green -Platform PlayMode -Filter 'Game.Tests.RouteSpawnTests'
"done" | Set-Content "$d\green-all.done"
