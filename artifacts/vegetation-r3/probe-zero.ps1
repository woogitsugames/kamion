$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
pwsh $slot -Acquire -Owner gpt-vegetation -StaleHours 1000000 -PollSeconds 10
if ($LASTEXITCODE -ne 0) { throw 'Unity slot acquisition failed' }
try {
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Width 1024 -Height 768 -Gate3 artifacts/vegetation-r3/photo-cameras-2048x1536.json -Cameras sbs-g3-b-297817221966185 -OutputDir artifacts/vegetation-r3/ablation-zero/Low-overcast-photo-2048x1536 *> artifacts/vegetation-r3/probe-zero.log
    if ($LASTEXITCODE -ne 0) { throw 'Zero-tree probe failed' }
} finally {
    pwsh $slot -Release -Owner gpt-vegetation
    git restore --worktree -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
