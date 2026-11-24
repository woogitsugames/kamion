$wt='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\rut-far-s24'; Set-Location $wt
$a="$wt\artifacts\rut-far-s24"; $o='rut-far-s24-t'
& pwsh -NoProfile -File "$wt\scripts\unity-slot.ps1" -Acquire -Pool unity -Owner $o
try { & pwsh -NoProfile -File "$wt\scripts\test.ps1" -Platform EditMode -BuildTarget Win64 -Filter 'AsphaltScopeTests|RoadPaintLaneFieldTests|RoadWearUvContractTests|WorldPbrTintTests' *> "$a\run5.log"; "tests exit=$LASTEXITCODE" | Out-File "$a\run5.status" }
finally { & git checkout -- game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat 2>$null
 & pwsh -NoProfile -File "$wt\scripts\unity-slot.ps1" -Release -Pool unity -Owner $o }
"DONE" | Add-Content "$a\run5.status"
