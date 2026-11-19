# dk19-tiles-s24 r4 (19.11): Unity import x3 + VQA + EditMode + pytest after merge f1c213a76 (r3 worlds kept: route_obstacles 0 colliders)
$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dk19-tiles-s24'; Set-Location $wt
$st = "$wt\artifacts\dk19-tiles-s24\jobs\r4.status"; $logd = "$wt\artifacts\logs"
"start $(Get-Date -Format s)" | Set-Content $st
function Step($name, [scriptblock]$b) { & $b *> "$logd\dk19-r4-$name.log"; "$name exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st }
while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -MaxSlots 2 -Owner dk19-r4-unity | Out-Null
foreach ($t in 'wygoda','bojary','mickiewicza') { Step "import-$t" { pwsh scripts/import-region.ps1 -Region "bialystok-$t" -BuildTarget Win64 } }
Step 'vqa-mickiewicza' { pwsh scripts/visual-qa.ps1 -Scene World_bialystok-mickiewicza -Tier High -Lighting overcast -BuildTarget Win64 -OutputDir artifacts/dk19-tiles-s24/vqa-r4/mickiewicza }
Step 'editmode' { pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 }
pwsh scripts/unity-slot.ps1 -Release -Owner dk19-r4-unity | Out-Null
git checkout -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat art-source/world 2>$null
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -MaxSlots 3 -Owner dk19-r4-pytest | Out-Null
Step 'pytest' { uv run --project tools/worldgen pytest tests/gis -q -p no:cacheprovider }
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner dk19-r4-pytest | Out-Null
"DONE exit=0 $(Get-Date -Format s)" | Add-Content $st
