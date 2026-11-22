# Po łańcuchach A/B/C: route_links, tile_graph, katalog (+--check), seams, route_obstacles, commit+push, pytest tests/gis. -> final.status
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$env:PYTHONIOENCODING = 'utf-8'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\regen-wave-7-s24'
$main = 'C:\Users\matma\Documents\Claude\kamion'
$o = "$wt\artifacts\regen-wave-7-s24"; $st = "$o\final.status"; $L = "$o\logs"
Set-Location $wt
function S($m) { Add-Content $st "$(Get-Date -Format s) $m" }
Start-Sleep 60
while (-not (Test-Path "$o\chain.status") -or @(Select-String 'chain=. DONE' "$o\chain.status").Count -lt 3) { Start-Sleep 60 }
S 'chains DONE'
# redo tiles (redo.txt) must have a chain=R line too
foreach ($r in (Get-Content "$o\redo.txt" -ErrorAction SilentlyContinue | Where-Object { $_.Trim() })) { while (-not (Select-String "$o\chain.status" -Pattern ("chain=R tile=" + [regex]::Escape($r) + " ") -Quiet)) { Start-Sleep 60 } }
S 'redo DONE'
pwsh -NoProfile -File "$o\commit.ps1" *>> "$o\autocommit.log"
pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Acquire -Pool heavy -Owner rw7-final *>> "$L\final-slot.log"
uv run --project tools/worldgen python tools/worldgen/streaming/route_links.py *> "$L\route_links.log"; S "route_links exit=$LASTEXITCODE"
uv run --project tools/worldgen python tools/worldgen/streaming/tile_graph.py *> "$L\tile_graph.log"; S "tile_graph exit=$LASTEXITCODE"
uv run --project tools/worldgen python scripts/export-region-catalog.py *> "$L\catalog.log"; S "catalog exit=$LASTEXITCODE"
uv run --project tools/worldgen python scripts/export-region-catalog.py --check *>> "$L\catalog.log"; S "catalog --check exit=$LASTEXITCODE"
uv run --project tools/worldgen python -m tools.worldgen.qa.seams --json "$o\seams_after.json" --md "$o\seams_after.md" *> "$L\seams_after.log"; S "seams exit=$LASTEXITCODE"
uv run --project tools/worldgen python tools/worldgen/qa/route_obstacles.py --out "$o\route_obstacles.json" *> "$L\route_obstacles.log"; S "route_obstacles exit=$LASTEXITCODE"
git add -- game/Assets/_Project/World/Runtime/Streaming/Resources/WorldStreaming
git add -A -- Data game/Assets/_Project/UI/Resources/CabDisplay/Nav game/Assets/_Project/Gameplay/Resources/Regions
git commit -qm "wip(regen-wave-7-s24): fala 7 (po ADR 0323-0326, przed buildem #5): route_links, tile_graph, katalog d67-full 54 (C, Maczka, Tykocin z 0326)`n`nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
git push -q -u origin HEAD 2>&1 | Out-Null
S "committed $(git rev-parse --short HEAD)"
uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider *> "$L\pytest.log"; S "pytest exit=$LASTEXITCODE"
pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Release -Pool heavy -Owner rw7-final *>> "$L\final-slot.log"
S 'DONE'
