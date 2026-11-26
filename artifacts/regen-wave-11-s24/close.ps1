# Domkniecie fali 11 po przebudowie C: route_links, tile_graph, katalog, seams, route_obstacles, pytest (5 + -k).
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$env:PYTHONIOENCODING = 'utf-8'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\regen-wave-11-s24'; $main = 'C:\Users\matma\Documents\Claude\kamion'
$o = "$wt\artifacts\regen-wave-11-s24"; $st = "$o\close.status"; $L = "$o\logs"
Set-Location $wt
function S($m) { Add-Content $st "$(Get-Date -Format s) $m" }
pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Acquire -Pool heavy -Owner rw11-close *>> "$L\close-slot.log"
uv run --project tools/worldgen python tools/worldgen/streaming/route_links.py *> "$L\route_links-close.log"; S "route_links exit=$LASTEXITCODE"
uv run --project tools/worldgen python tools/worldgen/streaming/tile_graph.py *> "$L\tile_graph-close.log"; S "tile_graph exit=$LASTEXITCODE"
uv run --project tools/worldgen python scripts/export-region-catalog.py *> "$L\catalog-close.log"; S "catalog exit=$LASTEXITCODE"
uv run --project tools/worldgen python scripts/export-region-catalog.py --check *>> "$L\catalog-close.log"; S "catalog --check exit=$LASTEXITCODE"
uv run --project tools/worldgen python -m tools.worldgen.qa.seams --json "$o\seams_close.json" --md "$o\seams_close.md" *> "$L\seams-close.log"; S "seams exit=$LASTEXITCODE"
uv run --project tools/worldgen python tools/worldgen/qa/route_obstacles.py --out "$o\route_obstacles_close.json" *> "$L\route_obstacles-close.log"; S "route_obstacles exit=$LASTEXITCODE"
uv run --project tools/worldgen python -m pytest -q -p no:cacheprovider tests/gis/test_budget_0221.py::test_region_c_frame_budget_has_margin tests/gis/test_hero_bridge.py::test_asset_lods_and_budget "tests/gis/test_ring_0231.py::test_authored_files_present_and_consistent[dw671-tykocin-03]" "tests/gis/test_typology_0238.py::test_triangle_budget_is_not_above_the_baseline[bialystok-industrial-c]" tests/gis/test_world_v31.py::test_frame_budget_with_forest_hlod *> "$L\pytest-five.log"; S "pytest five exit=$LASTEXITCODE"
uv run --project tools/worldgen python -m pytest -q -p no:cacheprovider tests/gis -k "budget or typology or world_v31 or hero_bridge or ring_0231 or trees_0347 or far_field or seam or furniture" *> "$L\pytest-k.log"; S "pytest -k exit=$LASTEXITCODE"
pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Release -Pool heavy -Owner rw11-close *>> "$L\close-slot.log"
S 'DONE'
