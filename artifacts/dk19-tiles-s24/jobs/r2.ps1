# dk19-tiles-s24 r2 (18.11): rebuild after merge of main (knyszyn-r24: wood_planks set_tile_m, despike_arcs by distance)
$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dk19-tiles-s24'; Set-Location $wt
$st = "$wt\artifacts\dk19-tiles-s24\jobs\r2.status"; $logd = "$wt\artifacts\logs"
"start $(Get-Date -Format s)" | Set-Content $st
function Step($name, [scriptblock]$b) { & $b *> "$logd\dk19-r2-$name.log"; "$name exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st }
foreach ($t in 'bojary','mickiewicza','wygoda') {
  pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -MaxSlots 3 -Owner "dk19-r2-$t" | Out-Null
  Step "world-$t" { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region "bialystok-$t" --context }
  Step "fidelity-$t" { uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region "bialystok-$t" }
  Step "route-$t" { uv run --project tools/worldgen python scripts/export-route.py --region "bialystok-$t" }
  pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner "dk19-r2-$t" | Out-Null
}
Step 'route_links' { uv run --project tools/worldgen python tools/worldgen/streaming/route_links.py }
Step 'tile_graph' { uv run --project tools/worldgen python tools/worldgen/streaming/tile_graph.py }
Step 'catalog' { uv run --no-project python scripts/export-region-catalog.py --check }
git checkout -- Data/Regions/bialystok-industrial-c Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json 2>$null
while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -MaxSlots 2 -Owner dk19-r2-unity | Out-Null
foreach ($t in 'wygoda','bojary','mickiewicza') { Step "import-$t" { pwsh scripts/import-region.ps1 -Region "bialystok-$t" -BuildTarget Win64 } }
Step 'vqa-mickiewicza' { pwsh scripts/visual-qa.ps1 -Scene World_bialystok-mickiewicza -Tier High -Lighting overcast -BuildTarget Win64 -OutputDir artifacts/dk19-tiles-s24/vqa-r2/mickiewicza }
Step 'editmode' { pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 }
pwsh scripts/unity-slot.ps1 -Release -Owner dk19-r2-unity | Out-Null
git checkout -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat 2>$null
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -MaxSlots 3 -Owner dk19-r2-pytest | Out-Null
Step 'pytest' { uv run --project tools/worldgen pytest tests/gis -q -p no:cacheprovider }
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner dk19-r2-pytest | Out-Null
"DONE exit=0 $(Get-Date -Format s)" | Add-Content $st
