# build_world (heavy slot) -> import-region + AFTER renders + EditMode (unity slot); status lines in artifacts/logs/chain.status
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\atlas-0184'
Set-Location $wt
$logs = Join-Path $wt 'artifacts\logs'; $st = Join-Path $logs 'chain.status'
function Mark($m) { "$m $(Get-Date -Format s)" | Out-File $st -Append -Encoding utf8 }
function Restore { git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>&1 | Out-Null }
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner atlas-0184
try {
  uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> (Join-Path $logs 'build_world.log')
  $bw = $LASTEXITCODE; Mark "build_world exit $bw"
} finally { pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Pool heavy -Owner atlas-0184 }
if ($bw -ne 0) { Mark 'CHAIN STOP'; exit 1 }
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner atlas-0184
try {
  pwsh -NoProfile -File scripts/import-region.ps1 -Region bialystok-industrial-c *> (Join-Path $logs 'import.log')
  $ic = $LASTEXITCODE; Restore; Mark "import exit $ic"
  if ($ic -eq 0) {
    $cams = 'r10_block_1,r10_block_2,r10_block_3,r10_block_4,r10_block_5,r10_office_2'
    foreach ($s in 'Low:overcast', 'Low:clear', 'High:overcast') {
      $t, $l = $s.Split(':')
      pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier $t -Lighting $l -Gate3 Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json -Cameras $cams -OutputDir "artifacts/atlas-0184/after/$t-$l" *> (Join-Path $logs "after-$t-$l.log")
      Mark "render after $t-$l exit $LASTEXITCODE"; Restore
    }
    pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode *> (Join-Path $logs 'editmode.log')
    Mark "editmode exit $LASTEXITCODE"; Restore
  }
} finally { pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner atlas-0184; Restore; Mark 'CHAIN DONE' }
