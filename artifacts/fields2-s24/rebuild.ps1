param([string]$Tiles = 'knyszyn-w,dk65-07')
Set-Location C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\fields2-s24
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner fields2-s24
try { foreach ($t in $Tiles.Split(',')) { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $t *> "artifacts/fields2-s24/logs/build_$t.log"; "exit $t $LASTEXITCODE" } }
finally { pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner fields2-s24 }
"DONE rebuild"
