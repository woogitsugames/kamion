param(
    [Parameter(Mandatory)] [ValidateSet('World', 'Materials', 'GisFinal')] [string]$Task,
    [string[]]$TaskArgs = @()
)
$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
# This worktree predates the new heavy pool. Read the current owning script on
# main directly, without editing or committing shared infrastructure files.
$slotScript = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$heavyOwner = (git -c core.fsmonitor=false branch --show-current).Trim()
if ($LASTEXITCODE -ne 0 -or $heavyOwner -notlike 'gpt-vegetation-r*') { throw 'Wrong vegetation branch' }
pwsh $slotScript -Acquire -Pool heavy -Owner $heavyOwner -StaleHours 1000000
if ($LASTEXITCODE -ne 0) { throw 'Heavy slot acquisition failed' }
$jobExit = 1
try {
    switch ($Task) {
        'World' { uv run --project tools/worldgen python -u tools/worldgen/roads/build_world.py --region bialystok-industrial-c @TaskArgs }
        'Materials' { uv run --project tools/worldgen python -u art-source/world/materials/_src/build_all.py @TaskArgs }
        'GisFinal' { uv run --project tools/worldgen python -m pytest tests/gis -q @TaskArgs }
    }
    $jobExit = $LASTEXITCODE
} finally {
    pwsh $slotScript -Release -Pool heavy -Owner $heavyOwner
}
exit $jobExit
