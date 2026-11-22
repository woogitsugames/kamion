param([string]$Tile)
# Redo one wave-7 tile (after a generator fix); writes a normal chain.status line (chain=R) so build #4 picks it up.
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$env:PYTHONIOENCODING = 'utf-8'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\regen-wave-7-s24'; $main = 'C:\Users\matma\Documents\Claude\kamion'
$out = "$wt\artifacts\regen-wave-7-s24"; Set-Location $wt
$log = "$out\logs\$Tile-redo.log"; $owner = "regen-wave-7-s24-R"
pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Acquire -Pool heavy -Owner $owner *>> $log
$t0 = Get-Date
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $Tile --context *>> $log; $e1 = $LASTEXITCODE; $t1 = Get-Date
uv run --project tools/worldgen python scripts/export-route.py --region $Tile *>> $log; $e2 = $LASTEXITCODE
uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region $Tile *>> $log; $e3 = $LASTEXITCODE; $t2 = Get-Date
pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Release -Pool heavy -Owner $owner *>> $log
Add-Content "$out\chain.status" ("{0} chain=R tile={1} build_exit={2} route_exit={3} fidelity_exit={4} build_s={5:N0} total_s={6:N0}" -f (Get-Date -Format s), $Tile, $e1, $e2, $e3, ($t1 - $t0).TotalSeconds, ($t2 - $t0).TotalSeconds)
