$ErrorActionPreference = 'Stop'
$root = 'C:\Users\matma\Documents\Claude\kamion'
Set-Location (Join-Path $root '.claude\worktrees\review-0153')
$slot = Join-Path $root 'scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Pool heavy -Owner review-0153
try {
    $t = Get-Date
    uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> artifacts/review-0153/build-world.log
    "build_world exit $LASTEXITCODE $([int]((Get-Date)-$t).TotalSeconds)s" | Add-Content artifacts/review-0153/regen-exit.txt
} finally { & pwsh $slot -Release -Pool heavy -Owner review-0153 }
