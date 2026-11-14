param([string]$Region, [string]$Tag = 'r2', [string]$Tiers = 'Low')
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot\..\..
$A = "artifacts/knyszyn-0204"; $st = "$A/full_${Region}_$Tag.status"
"start $(Get-Date -Format s)" | Set-Content $st
$env:PYTHONUNBUFFERED = '1'
uv run --project tools/worldgen tools/worldgen/build_region.py --region $Region *> "$A/build_region_${Region}_$Tag.log"
"build_region exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
if ($LASTEXITCODE -eq 0) {
  pwsh -NoProfile -File "$A/chain_world.ps1" -Region $Region
  Get-Content "$A/world_$Region.status" | Add-Content $st
  if ((Get-Content "$A/world_$Region.status" -Raw) -match 'build_world exit=0') {
    pwsh -NoProfile -File "$A/chain_unity.ps1" -Region $Region -Tag $Tag -Tiers $Tiers
    Get-Content "$A/unity_${Region}_$Tag.status" | Add-Content $st
  }
}
"FULL DONE $(Get-Date -Format s)" | Add-Content $st
