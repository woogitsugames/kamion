$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
pwsh $slot -Acquire -Owner gpt-vegetation -StaleHours 1000000 -PollSeconds 10
if ($LASTEXITCODE -ne 0) { throw 'Unity slot acquisition failed' }
$jobExit = 1
try {
    pwsh scripts/test.ps1 -Platform EditMode
    $jobExit = $LASTEXITCODE
} finally {
    pwsh $slot -Release -Owner gpt-vegetation
    git restore --worktree -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
exit $jobExit
