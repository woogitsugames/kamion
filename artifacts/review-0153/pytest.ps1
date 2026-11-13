$root = 'C:\Users\matma\Documents\Claude\kamion'
Set-Location (Join-Path $root '.claude\worktrees\review-0153')
$slot = Join-Path $root 'scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Pool heavy -Owner review-0153
try {
  uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider *> artifacts/review-0153/pytest-gis.log
  "pytest exit $LASTEXITCODE" | Add-Content artifacts/review-0153/pytest-exit.txt
} finally { & pwsh $slot -Release -Pool heavy -Owner review-0153 }
