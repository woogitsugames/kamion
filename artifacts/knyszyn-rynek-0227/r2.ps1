$ErrorActionPreference = 'Stop'
Set-Location 'C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/knyszyn-rynek-0227'
$owner = 'knyszyn-rynek-0227'
function Check-Disk { if ((Get-PSDrive C).Free -lt 60GB) { throw 'C below 60 GiB' } }
function Run-Checked { param([scriptblock]$Action) & $Action; if ($LASTEXITCODE -ne 0) { throw "Command failed: $LASTEXITCODE" } }
try {
 Check-Disk
 Run-Checked { pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $owner }
 try { Run-Checked { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region knyszyn } }
 finally { pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner $owner }
 Check-Disk
 Run-Checked { pwsh scripts/unity-slot.ps1 -Acquire -Owner $owner }
 try {
  if (Test-Path C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN) { throw 'PHONE_RUN appeared after slot acquisition' }
  Run-Checked { pwsh scripts/import-region.ps1 -Region knyszyn }
 } finally { pwsh scripts/unity-slot.ps1 -Release -Owner $owner }
 foreach ($tier in @('Low','High')) { foreach ($lighting in @('clear','dusk')) {
  Check-Disk
  Run-Checked { pwsh scripts/unity-slot.ps1 -Acquire -Owner $owner }
  try {
   if (Test-Path C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN) { throw 'PHONE_RUN appeared after slot acquisition' }
   Run-Checked { pwsh scripts/visual-qa.ps1 -Scene World_knyszyn -Tier $tier -Lighting $lighting -Width 1920 -Height 1080 -OutputDir "artifacts/knyszyn-rynek-0227/r2/$tier-$lighting" }
  } finally { pwsh scripts/unity-slot.ps1 -Release -Owner $owner }
 } }
 'OK' | Set-Content artifacts/knyszyn-rynek-0227/r2.done
} catch { $_ | Out-String | Set-Content artifacts/knyszyn-rynek-0227/r2.done; exit 1 }


