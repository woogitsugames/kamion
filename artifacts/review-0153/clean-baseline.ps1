$root = 'C:\Users\matma\Documents\Claude\kamion'
Set-Location (Join-Path $root '.claude\worktrees\review-0153')
$slot = Join-Path $root 'scripts/unity-slot.ps1'
$log = 'artifacts/review-0153/clean.txt'
while (-not (Select-String -Path artifacts/review-0153/post.txt -Pattern 'DONE post' -Quiet -ErrorAction SilentlyContinue)) { Start-Sleep 30 }
while (-not (Test-Path artifacts/review-0153/pytest-exit.txt)) { Start-Sleep 30 }
# clean baseline: main code (same main sha as merge parent) regenerated + imported here
Copy-Item -Recurse -Force artifacts/review-0153 "$env:TEMP\review-0153-artifacts-keep"
git add -f artifacts/review-0153/*.ps1 artifacts/review-0153/*.txt artifacts/review-0153/*.tsv artifacts/review-0153/*/*/stats.txt artifacts/review-0154-before/*/stats.txt; git commit -q -m "wip(review-0153): after renders, 0154 baseline, EditMode (before clean-baseline switch)`n`nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git switch --detach -q 85d2030d5
"switched to main 85d2030d5: $(git rev-parse --short HEAD)" | Add-Content "$env:TEMP\review-0153-clean.txt"
& pwsh $slot -Acquire -Pool heavy -Owner review-0153
try {
  uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> "$env:TEMP\review-0153-clean-build.log"
  "build_world main exit $LASTEXITCODE" | Add-Content "$env:TEMP\review-0153-clean.txt"
} finally { & pwsh $slot -Release -Pool heavy -Owner review-0153 }
& pwsh $slot -Acquire -Owner review-0153
try {
  & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> "$env:TEMP\review-0153-clean-import.log"
  "import main exit $LASTEXITCODE" | Add-Content "$env:TEMP\review-0153-clean.txt"
} finally { git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings; & pwsh $slot -Release -Owner review-0153 }
foreach ($tier in 'Low','High') {
  & pwsh $slot -Acquire -Owner review-0153
  try {
    & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting clear -Gate3 Data/Regions/bialystok-industrial-c/gate3_cameras.json -OutputDir "$env:TEMP\review-0153-before-clean\$tier-clear" *> "$env:TEMP\review-0153-clean-$tier.log"
    "render clean $tier exit $LASTEXITCODE" | Add-Content "$env:TEMP\review-0153-clean.txt"
  } finally { git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings; & pwsh $slot -Release -Owner review-0153 }
}
git checkout -q -- .
git switch -q review-0153
Copy-Item -Recurse -Force "$env:TEMP\review-0153-before-clean" artifacts/review-0153/before-clean
Get-Content "$env:TEMP\review-0153-clean.txt" | Add-Content $log
"DONE clean (worktree _Generated/Data now = main code world)" | Add-Content $log


