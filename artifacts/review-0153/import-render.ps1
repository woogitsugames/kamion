$ErrorActionPreference = 'Continue'
$root = 'C:\Users\matma\Documents\Claude\kamion'
$wt = Join-Path $root '.claude\worktrees\review-0153'
Set-Location $wt
$slot = Join-Path $root 'scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Owner review-0153
try {
  & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> artifacts/review-0153/import.log
  "import exit $LASTEXITCODE" | Add-Content artifacts/review-0153/import-exit.txt
} finally {
  git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
  & pwsh $slot -Release -Owner review-0153
}
& pwsh artifacts/review-0153/render.ps1 -Stage after
