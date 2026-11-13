$ErrorActionPreference = 'Continue'
$root = 'C:\Users\matma\Documents\Claude\kamion'
Set-Location (Join-Path $root '.claude\worktrees\review-0154')
$slot = Join-Path $root 'scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Pool heavy -Owner review-0154
try {
    $t = Get-Date
    uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> artifacts/review-0154/build-world.log
    "build_world exit $LASTEXITCODE $([int]((Get-Date)-$t).TotalSeconds)s" | Add-Content artifacts/review-0154/progress.txt
} finally { & pwsh $slot -Release -Pool heavy -Owner review-0154 }
& pwsh $slot -Acquire -Owner review-0154
try {
  if (Test-Path "$root/artifacts/locks/PHONE_RUN") { throw 'PHONE_RUN' }
  & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> artifacts/review-0154/import.log
  "import exit $LASTEXITCODE" | Add-Content artifacts/review-0154/progress.txt
} finally {
  git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
  & pwsh $slot -Release -Owner review-0154
}
foreach ($tier in 'Low','High') {
  & pwsh $slot -Acquire -Owner review-0154
  try {
    if (Test-Path "$root/artifacts/locks/PHONE_RUN") { throw 'PHONE_RUN' }
    & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting clear -Gate3 artifacts/gpt-s16-r2/qa-cameras.json -OutputDir "artifacts/review-0154/after/$tier-clear" *> "artifacts/review-0154/after-$tier.log"
    "render after $tier exit $LASTEXITCODE" | Add-Content artifacts/review-0154/progress.txt
  } finally {
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slot -Release -Owner review-0154
  }
}
"DONE after" | Add-Content artifacts/review-0154/progress.txt
