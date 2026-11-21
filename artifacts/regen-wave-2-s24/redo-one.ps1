param([string]$Tile = "dk65-06", [switch]$NoFinal)
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\regen-wave-2-s24'; $main = 'C:\Users\matma\Documents\Claude\kamion'
$o = "$wt\artifacts\regen-wave-2-s24"; Set-Location $wt
$log = "$o\logs\$Tile-redo.log"
pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Acquire -Pool heavy -Owner rw2-redo *>> $log
$t0 = Get-Date
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $Tile --context *>> $log; $e1 = $LASTEXITCODE; $t1 = Get-Date
uv run --project tools/worldgen python scripts/export-route.py --region $Tile *>> $log; $e2 = $LASTEXITCODE
uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region $Tile *>> $log; $e3 = $LASTEXITCODE
pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Release -Pool heavy -Owner rw2-redo *>> $log
Add-Content "$o\chain.status" ("{0} chain=R tile={1} build_exit={2} route_exit={3} fidelity_exit={4} build_s={5:N0} total_s={6:N0}" -f (Get-Date -Format s), $Tile, $e1, $e2, $e3, ($t1-$t0).TotalSeconds, ((Get-Date)-$t0).TotalSeconds)
if ($e1 -eq 0 -and -not $NoFinal) { Start-Process pwsh -ArgumentList "-NoProfile","-File","$o\final.ps1" -WindowStyle Hidden }
