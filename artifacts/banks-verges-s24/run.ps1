param([Parameter(Mandatory)][string]$Round, [switch]$Build, [switch]$SkipImport, [string]$Regions = 'tykocin,dk65-07,knyszyn-w', [string]$Tiers = 'High', [switch]$LowStats, [switch]$Tests, [switch]$BuildOnly, [switch]$VqaOnly, [string]$Lightings = 'clear,overcast')
$ErrorActionPreference = 'Continue'
$main = 'C:\Users\matma\Documents\Claude\kamion'
$wt = "$main\.claude\worktrees\banks-verges-s24"
Set-Location $wt
$a = "$wt\artifacts\banks-verges-s24"
$log = "$a\logs"; New-Item -ItemType Directory -Force $log | Out-Null
$st = "$log\$Round.status"
"START $(Get-Date -f s) build=$Build buildOnly=$BuildOnly vqaOnly=$VqaOnly" | Add-Content $st
$regs = $Regions -split ','
$owner = 'banks-verges-s24'
if ($Build) {
  pwsh -NoProfile -File $main\scripts\unity-slot.ps1 -Acquire -Pool heavy -Owner $owner
  foreach ($r in $regs) {
    if ($r -eq 'tykocin') {
      uv run --project tools/worldgen python tools/worldgen/streetscape/water_banks.py --region $r *> "$log\$Round-water_banks-$r.log"
      "water_banks $r exit=$LASTEXITCODE $(Get-Date -f s)" | Add-Content $st
    }
    uv run --project tools/worldgen python -u tools/worldgen/roads/build_world.py --region $r *> "$log\$Round-build_world-$r.log"
    "build_world $r exit=$LASTEXITCODE $(Get-Date -f s)" | Add-Content $st
  }
  pwsh -NoProfile -File $main\scripts\unity-slot.ps1 -Release -Pool heavy -Owner $owner
}
if ($BuildOnly) { "BUILD DONE $(Get-Date -f s)" | Add-Content $st; exit 0 }
while (Test-Path $main\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
pwsh -NoProfile -File $main\scripts\unity-slot.ps1 -Acquire -Owner $owner
if (-not $SkipImport -and -not $VqaOnly) {
  foreach ($r in $regs) {
    pwsh -NoProfile -File scripts/import-region.ps1 -Region $r -Tiers $Tiers -BuildTarget Win64 *> "$log\$Round-import-$r.log"
    "import $r exit=$LASTEXITCODE $(Get-Date -f s)" | Add-Content $st
  }
}
$cams = @{
  'tykocin'   = 'water_bank_bridge_se,water_oblique_bridge,water_boat_under_bridge,top_water_bridge,look_narew_truss_side,limit_b16_bridge_n_060m,bv_cab_bridge_n,bv_cab_bridge_river,bv_cab_bridge_side,bv_bank_se,bv_bank_sw,bv_bank_close,bv_bank_n'
  'dk65-07'   = 'drive_wood,drive_kozince,rev_kozince,top_kozince,bv_side_wood,bv_air_wood,bv_cab_s242,bv_verge_close'
  'knyszyn-w' = 'dk65_fields_nw,dk65_north_edge_in,dk65_polna,dk65_goniadzka,goniadzka_above,bv_side_ditch,bv_ditch_close,bv_cab_s1701,bv_air_fields'
}
foreach ($r in $regs) {
  foreach ($l in ($Lightings -split ',')) {
    pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene "World_${r}_High" -Tier High -Lighting $l -Width 1920 -Height 1080 -Cameras $cams[$r] -Gate3 "$a\cams-$r.json" -BuildTarget Win64 -OutputDir "$a\$Round\$r-High-$l" *> "$log\$Round-vqa-$r-$l.log"
    "vqa $r $l exit=$LASTEXITCODE $(Get-Date -f s)" | Add-Content $st
  }
  if ($LowStats) {
    pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene "World_${r}" -Tier Low -Lighting clear -Width 1920 -Height 1080 -Cameras $cams[$r] -Gate3 "$a\cams-$r.json" -BuildTarget Win64 -OutputDir "$a\$Round\$r-Low-clear" *> "$log\$Round-vqa-$r-low.log"
    "vqa $r Low exit=$LASTEXITCODE $(Get-Date -f s)" | Add-Content $st
  }
}
if ($Tests) {
  pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode -BuildTarget Win64 *> "$log\$Round-editmode.log"
  "editmode exit=$LASTEXITCODE $(Get-Date -f s)" | Add-Content $st
}
pwsh -NoProfile -File $main\scripts\unity-slot.ps1 -Release -Owner $owner
git -C $wt checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
"DONE $(Get-Date -f s)" | Add-Content $st
