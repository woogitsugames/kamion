$ErrorActionPreference='Stop'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
. artifacts/vegetation-r1/checkpoint.ps1
$slot='C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
pwsh $slot -Acquire -Owner gpt-vegetation -StaleHours 1000000 -PollSeconds 10
if($LASTEXITCODE -ne 0){throw 'Unity slot failed'}
try {
 pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Cameras 'route-onramp-andersa-above,route-putry-approach,g3a-rondo-bie-approach,dk8-dk19-exit,r10_fence_2,driver-andersa-to-putry,photo-biezenstwa-ground,fire-station-ref7197' -Gate3 Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json -OutputDir artifacts/vegetation-r1/probe-b/Low-overcast *> artifacts/vegetation-r1/probe-b.log
 if($LASTEXITCODE -ne 0){throw 'Probe B failed'}
} finally {
 pwsh $slot -Release -Owner gpt-vegetation
 git restore --worktree -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
Add-Content artifacts/vegetation-r1/STATUS.md 'Zapisano osiem próbnych kamer wariantu B Low overcast. Następny krok: obejrzeć i zmierzyć grass-only przed decyzją o pełnej macierzy.'
Save-VegetationCheckpoint -Message 'wip(vegetation): probe B Low overcast'
exit 0
