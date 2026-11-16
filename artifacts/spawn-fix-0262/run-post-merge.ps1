$d = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\spawn-fix-0262\artifacts\spawn-fix-0262'
Remove-Item "$d\post-merge.done" -ErrorAction SilentlyContinue
pwsh -NoProfile -File "$d\run-editmode.ps1" -Tag post-merge -Filter 'Game.Tests.StartClearanceTests;Game.Tests.RegionSelectTests'
pwsh -NoProfile -File "$d\run-editmode.ps1" -Tag playmode-post-merge -Platform PlayMode -Filter 'Game.Tests.RouteSpawnTests'
"done" | Set-Content "$d\post-merge.done"
