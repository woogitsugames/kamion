$root = 'C:\Users\matma\Documents\Claude\kamion'
Set-Location (Join-Path $root '.claude\worktrees\review-0154')
$slot = Join-Path $root 'scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Pool heavy -Owner review-0154
try {
  uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider *> artifacts/review-0154/pytest-gis.log
  "pytest exit $LASTEXITCODE" | Add-Content artifacts/review-0154/tests.txt
} finally { & pwsh $slot -Release -Pool heavy -Owner review-0154 }
while (-not (Select-String -Path artifacts/review-0154/progress.txt -Pattern 'DONE after' -Quiet)) { Start-Sleep 30 }
& pwsh $slot -Acquire -Owner review-0154
try {
  & pwsh scripts/test.ps1 -Platform EditMode *> artifacts/review-0154/editmode.log
  "editmode exit $LASTEXITCODE" | Add-Content artifacts/review-0154/tests.txt
} finally { git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings; & pwsh $slot -Release -Owner review-0154 }
"DONE tests" | Add-Content artifacts/review-0154/tests.txt
