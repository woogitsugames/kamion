# ADR 0207: per tile build_world (+export-route) under the heavy slot, then import + visual-qa Low (High with -High)
# under the unity slot. Status: artifacts/dk65-tiles-0207/logs/chain.status (end line "CHAIN DONE <tag>").
param([string[]]$Tiles = @('dk65-02'), [string]$Tag = 'r1', [switch]$NoWorld, [switch]$NoImport, [switch]$High)
$ErrorActionPreference = 'Continue'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$A = 'artifacts/dk65-tiles-0207'; $L = "$A/logs"; $st = "$L/chain.status"; $o = 'dk65-tiles-0207'
$phone = 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN'
function Step($name, $pool, [scriptblock]$b) {
  if ($pool -eq 'unity') { while (Test-Path $phone) { Start-Sleep 60 } }
  pwsh scripts/unity-slot.ps1 -Acquire -Pool $pool -Owner $o | Out-Null
  "$name start $(Get-Date -Format s)" | Add-Content $st
  & $b *> "$L/$name.log"
  "$name exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
  pwsh scripts/unity-slot.ps1 -Release -Pool $pool -Owner $o | Out-Null
  if ($pool -eq 'unity') { git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null }
}
$Tiles = @($Tiles | ForEach-Object { $_ -split "," } | Where-Object { $_ })
foreach ($t in $Tiles) {
  if (-not $NoWorld) {
    Step "world-$t-$Tag" heavy {
      uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $t --context
      if ($LASTEXITCODE -eq 0) { uv run --project tools/worldgen python scripts/export-route.py --region $t }
    }
  }
  if (-not $NoImport) {
    Step "import-$t-$Tag" unity { pwsh scripts/import-region.ps1 -Region $t }
    Step "vqa-low-$t-$Tag" unity { pwsh scripts/visual-qa.ps1 -Scene "World_$t" -Tier Low -Lighting clear -Width 1920 -Height 1080 -OutputDir "$A/$t/$Tag/Low-clear" }
    if ($High) { Step "vqa-high-$t-$Tag" unity { pwsh scripts/visual-qa.ps1 -Scene "World_$t" -Tier High -Lighting clear -Width 1920 -Height 1080 -OutputDir "$A/$t/$Tag/High-clear" } }
  }
}
"CHAIN DONE $Tag $($Tiles -join ',') $(Get-Date -Format s)" | Add-Content $st
