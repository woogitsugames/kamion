# dk19-tiles-s24 r5 (19.11): after merge of main bc45fde50 - C determinism + tile_graph + dk19 tests, then EditMode Win64
$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dk19-tiles-s24'; Set-Location $wt
$st = "$wt\artifacts\dk19-tiles-s24\jobs\r5.status"; $logd = "$wt\artifacts\logs"
"start $(Get-Date -Format s)" | Set-Content $st
function Step($name, [scriptblock]$b) { & $b *> "$logd\dk19-r5-$name.log"; "$name exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st }
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -MaxSlots 3 -Owner dk19-r5-pytest | Out-Null
Step 'pytest-sel' { uv run --project tools/worldgen pytest tests/gis/test_world_roads.py tests/gis/test_tile_graph_0235.py tests/gis/test_dk19_qa_s24.py tests/gis/test_route_links_s23.py tests/gis/test_start_clear_0262.py -q -p no:cacheprovider }
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner dk19-r5-pytest | Out-Null
while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -MaxSlots 2 -Owner dk19-r5-unity | Out-Null
Step 'editmode' { pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 }
pwsh scripts/unity-slot.ps1 -Release -Owner dk19-r5-unity | Out-Null
git checkout -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat art-source/world 2>$null
"DONE exit=0 $(Get-Date -Format s)" | Add-Content $st
