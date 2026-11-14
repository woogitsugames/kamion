$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\bollards-0183'
Set-Location $wt
$st = 'artifacts/logs/pipeline-r3b.status'
function S([string]$m) { "$(Get-Date -Format HH:mm:ss) $m" | Out-File -FilePath $st -Append }
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner bollards-0183 *>> artifacts/logs/slot-heavy.log
try { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-dojlidy *> artifacts/logs/bw-r3b.log; $c = $LASTEXITCODE }
finally { pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner bollards-0183 *>> artifacts/logs/slot-heavy.log }
S "build r3b exit=$c"
pwsh artifacts/bollards-0183/tools/run_unity.ps1 -Steps import,low,high -Tag r3b -Cams 'bollards-photo-13m,bollards-detail-2m,bollards-close-5m,bollards-cab-20m,bollards-along-8m,photo_P11-063'
S 'PIPELINE DONE'
