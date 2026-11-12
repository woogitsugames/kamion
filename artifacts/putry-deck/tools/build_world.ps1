# ADR 0133: generator run under the heavy slot (FIFO), log to artifacts/putry-deck/logs
$ErrorActionPreference = 'Stop'
$root = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\putry-deck'
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
New-Item -ItemType Directory -Force "$root\artifacts\putry-deck\logs" | Out-Null
& pwsh -NoProfile -File $slot -Acquire -Pool heavy -Owner claude-putry-deck
try {
    Push-Location $root
    & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *>&1 | Tee-Object "$root\artifacts\putry-deck\logs\build_world.log"
    if ($LASTEXITCODE -ne 0) { throw "build_world $LASTEXITCODE" }
} finally { Pop-Location; & pwsh -NoProfile -File $slot -Release -Pool heavy -Owner claude-putry-deck }
