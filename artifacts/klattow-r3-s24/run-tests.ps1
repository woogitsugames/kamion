$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\klattow-r3-s24'; Set-Location $wt
$d = "$wt\artifacts\klattow-r3-s24"; "start $(Get-Date -Format HH:mm:ss)" | Set-Content "$d\tests.status"
pwsh scripts/unity-slot.ps1 -Acquire -Owner klattow-r3-s24 | Out-Null
pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 *> "$d\editmode.log"; "editmode exit=$LASTEXITCODE $(Get-Date -Format HH:mm:ss)" | Add-Content "$d\tests.status"
pwsh scripts/unity-slot.ps1 -Release -Owner klattow-r3-s24 | Out-Null
git -C $wt checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner klattow-r3-s24 | Out-Null
uv run --project tools/worldgen python -m pytest tests/gis -q -k "klattow or far_facade or material or plots or pavement or sidewalk or overrides or network" -p no:cacheprovider *> "$d\pytest-related.log"; "pytest exit=$LASTEXITCODE $(Get-Date -Format HH:mm:ss)" | Add-Content "$d\tests.status"
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner klattow-r3-s24 | Out-Null
"done" | Add-Content "$d\tests.status"
