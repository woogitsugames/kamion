# dk19-tiles-s24 r6: re-import bojary/mickiewicza after merge bc45fde50 (scenes failed to open) + StartClearance/RegionSelect/streaming tests
$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dk19-tiles-s24'; Set-Location $wt
$st = "$wt\artifacts\dk19-tiles-s24\jobs\r6.status"; $logd = "$wt\artifacts\logs"
"start $(Get-Date -Format s)" | Set-Content $st
function Step($name, [scriptblock]$b) { & $b *> "$logd\dk19-r6-$name.log"; "$name exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st }
pwsh scripts/unity-slot.ps1 -Acquire -MaxSlots 2 -Owner dk19-r6-unity | Out-Null
foreach ($t in 'wygoda','bojary','mickiewicza') { Step "import-$t" { pwsh scripts/import-region.ps1 -Region "bialystok-$t" -BuildTarget Win64 } }
Step 'editmode' { pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 }
pwsh scripts/unity-slot.ps1 -Release -Owner dk19-r6-unity | Out-Null
git checkout -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat art-source/world 2>$null
"DONE exit=0 $(Get-Date -Format s)" | Add-Content $st
