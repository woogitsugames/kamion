# BEFORE of the LOD1 cameras: world built with the temporary pre-0184 strip, then the AFTER world restored and re-imported
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\atlas-0184'
Set-Location $wt
$logs = Join-Path $wt 'artifacts\logs'; $st = Join-Path $logs 'before-chain.status'
function Mark($m) { "$m $(Get-Date -Format s)" | Out-File $st -Append -Encoding utf8 }
$w = Join-Path $wt 'Data\raw\derived\bialystok-industrial-c\world'
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner atlas-0184
try {
  uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> (Join-Path $logs 'build_world_before.log')
  $bw = $LASTEXITCODE; Mark "build_world(before) exit $bw"
} finally { pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Pool heavy -Owner atlas-0184 }
git checkout -- tools/worldgen/streetscape/facade_atlas.py
if ($bw -eq 0) {
  pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner atlas-0184-imp
  try { pwsh -NoProfile -File scripts/import-region.ps1 -Region bialystok-industrial-c *> (Join-Path $logs 'import_before.log'); Mark "import(before) exit $LASTEXITCODE" }
  finally { pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner atlas-0184-imp }
  pwsh -NoProfile -File artifacts/atlas-0184/render2.ps1 -Tag before *> (Join-Path $logs 'render2_before.log'); Mark 'render2(before) done'
}
# restore the AFTER world
robocopy "${w}_after" $w /MIR /NFL /NDL /NJH /NJS /NP | Out-Null; Mark "restore world rc $LASTEXITCODE"
git checkout -- Data art-source
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner atlas-0184-imp
try { pwsh -NoProfile -File scripts/import-region.ps1 -Region bialystok-industrial-c *> (Join-Path $logs 'import_restore.log'); Mark "import(restore) exit $LASTEXITCODE" }
finally { pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner atlas-0184-imp; git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null }
pwsh -NoProfile -File artifacts/atlas-0184/render2.ps1 -Tag after2 -Sets 'Low:overcast' *> (Join-Path $logs 'render2_after2.log'); Mark 'BEFORE CHAIN DONE'
