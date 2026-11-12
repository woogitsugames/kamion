$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
. artifacts/vegetation-r3/checkpoint.ps1
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
pwsh $slot -Acquire -Owner gpt-vegetation -StaleHours 1000000 -PollSeconds 10
if ($LASTEXITCODE -ne 0) { throw 'Unity slot acquisition failed' }
try {
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Width 1024 -Height 768 -Gate3 artifacts/vegetation-r3/photo-cameras-2048x1536.json -Cameras sbs-g3-b-297817221966185 -OutputDir artifacts/vegetation-r3/probe/Low-overcast-photo-2048x1536 *> artifacts/vegetation-r3/probe-low.log
    if ($LASTEXITCODE -ne 0) { throw 'Low D51 probe failed' }
} finally {
    pwsh $slot -Release -Owner gpt-vegetation
    git restore --worktree -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
Add-Content artifacts/vegetation-r3/STATUS.md 'Zapisano próbę B/120 Low-overcast w tych samych 1024x768 i FOV co baseline. Następny krok: obejrzeć i porównać koszt, przed pełną macierzą.'
Save-VegetationCheckpoint -Message 'wip(vegetation): próba B120 Low po punktach drzew'
