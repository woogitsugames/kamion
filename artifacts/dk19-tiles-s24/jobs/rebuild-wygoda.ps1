# dk19-tiles-s24: after rebuild.ps1 DONE - rebuild wygoda (world predates main seam_p2a/markings), then streaming data again.
$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dk19-tiles-s24'
Set-Location $wt
$st = "$wt\artifacts\dk19-tiles-s24\jobs\rebuild-wygoda.status"
$logd = "$wt\artifacts\logs"
"wait $(Get-Date -Format s)" | Set-Content $st
while (-not (Select-String -Quiet -Path "$wt\artifacts\dk19-tiles-s24\jobs\rebuild.status" -Pattern '^DONE')) { Start-Sleep 60 }
"start $(Get-Date -Format s)" | Add-Content $st
function Step($name, [scriptblock]$b) {
  & $b *> "$logd\dk19-s24-$name.log"; $ec = $LASTEXITCODE
  "$name exit=$ec $(Get-Date -Format s)" | Add-Content $st
}
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -MaxSlots 3 -Owner "dk19-s24-wygoda" | Out-Null
Step 'world-wygoda' { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-wygoda --context }
Step 'fidelity-wygoda' { uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-wygoda }
Step 'route-wygoda' { uv run --project tools/worldgen python scripts/export-route.py --region bialystok-wygoda }
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner "dk19-s24-wygoda" | Out-Null
Step 'route_links2' { uv run --project tools/worldgen python tools/worldgen/streaming/route_links.py }
Step 'tile_graph2' { uv run --project tools/worldgen python tools/worldgen/streaming/tile_graph.py }
Step 'catalog2' { uv run --no-project python scripts/export-region-catalog.py --check }
"DONE exit=0 $(Get-Date -Format s)" | Add-Content $st
