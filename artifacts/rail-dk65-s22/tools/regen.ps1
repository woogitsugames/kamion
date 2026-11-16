# rail-dk65-s22 (s23): one joint regeneration after merging int-dk65-s22 (main) + #138 (ADR 0272).
#   -Mode world : heavy slot; per tile build_world --context (rail tiles dk65-01..04: + cams.py + second build so the
#                 rail_x* cameras are baked), commit + push generated per tile.
#   -Mode unity : unity slot; per tile waits for its world step, then import + visual-qa Low/High (all control cameras).
#   -Mode final : export-route per tile (diff only, no commit), export-region-catalog --check, pytest tests/gis (heavy
#                 slot), EditMode (unity slot). Waits for "WORLD DONE".
# Status: artifacts/rail-dk65-s22/logs/regen-<Mode>.status ; read every `exit=`, the DONE marker proves nothing.
param([string[]]$Tiles, [ValidateSet('world', 'unity', 'final')][string]$Mode = 'world', [string]$Tag = 'r3',
      [string]$Owner = 'rail-dk65-s22')
$ErrorActionPreference = 'Continue'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$A = 'artifacts/rail-dk65-s22'; $L = "$A/logs"; $st = "$L/regen-$Mode.status"; $wst = "$L/regen-world.status"
New-Item -ItemType Directory -Force $L | Out-Null
$main = 'C:\Users\matma\Documents\Claude\kamion'
$phone = "$main\artifacts\locks\PHONE_RUN"
$RailCams = @('dk65-01', 'dk65-02', 'dk65-03', 'dk65-04', 'dw671-tykocin-01')
function Step($name, [scriptblock]$b) {
  foreach ($try in 1..3) {       # exit -1073741502 = the process did not start: retry
    "$name start $(Get-Date -Format s)" | Add-Content $st
    $global:LASTEXITCODE = 0
    & $b *> "$L/$name.log"
    $code = $LASTEXITCODE
    "$name exit=$code $(Get-Date -Format s)" | Add-Content $st
    if ($code -ne -1073741502) { break }
    Copy-Item "$L/$name.log" "$L/$name.try$try.log" -Force; Start-Sleep 20
  }
  return ($code -eq 0)
}
function WorldExit($t) {
  if (-not (Test-Path $wst)) { return $null }
  $m = @(Get-Content $wst -ErrorAction SilentlyContinue | Where-Object { $_ -match "^tile-$t-$Tag exit=(-?\d+) " })
  if ($m.Count -eq 0) { return $null }
  [void]($m[-1] -match 'exit=(-?\d+) '); return [int]$Matches[1]
}
function Beat($pool) { $f = Get-Item "$main\artifacts\locks\$pool-slots\$Owner.slot" -ErrorAction SilentlyContinue; if ($f) { $f.LastWriteTime = Get-Date } }
$Tiles = @($Tiles | ForEach-Object { $_ -split "," } | Where-Object { $_ })
if ($Mode -eq 'world') {
  pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $Owner | Out-Null
  "heavy slot $(Get-Date -Format s)" | Add-Content $st
  foreach ($t in $Tiles) {
    $ok = Step "world-$t-$Tag" { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $t --context }
    Beat heavy
    if ($ok -and ($RailCams -contains $t) -and (Test-Path "Data/Regions/$t/generated/rail.json")) {
      $before = (Get-FileHash "Data/Regions/$t/control_cameras_place.authored.json").Hash
      $ok = Step "cams-$t-$Tag" { uv run --project tools/worldgen python artifacts/rail-dk65-s22/tools/cams.py $t }
      $ids = @((Get-Content "Data/Regions/$t/generated/control_cameras.json" -Raw | ConvertFrom-Json).cameras.id)
      $want = @((Get-Content "Data/Regions/$t/control_cameras_place.authored.json" -Raw | ConvertFrom-Json).cameras.id | Where-Object { $_ -like 'rail_x*' })
      $missing = @($want | Where-Object { $ids -notcontains $_ })
      if ($ok -and ($missing.Count -gt 0 -or $before -ne (Get-FileHash "Data/Regions/$t/control_cameras_place.authored.json").Hash)) {
        $ok = Step "world2-$t-$Tag" { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $t --context }
        Beat heavy
      }
    }
    if ($ok) {
      git add "Data/Regions/$t/generated" "Data/Regions/$t/control_cameras_place.authored.json" *>> "$L/git-$t.log"
      Get-ChildItem "Data/SourceManifests" -Filter "$t-*.json" -ErrorAction SilentlyContinue | ForEach-Object { git add $_.FullName *>> "$L/git-$t.log" }
      git commit -q -m "wip(rail-dk65-s22): generated $t (${Tag}: main int-dk65 + ADR 0272 + rail 0223/0268)`n`nCo-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>" *>> "$L/git-$t.log"
      git push -q origin rail-dk65-s22 *>> "$L/git-$t.log"
    }
    "tile-$t-$Tag exit=$(if ($ok) { 0 } else { 1 }) $(Get-Date -Format s)" | Add-Content $st
  }
  pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner $Owner | Out-Null
  "WORLD DONE $Tag $($Tiles -join ',') $(Get-Date -Format s)" | Add-Content $st
}
elseif ($Mode -eq 'unity') {
  $got = $false
  foreach ($t in $Tiles) {
    "wait tile-$t-$Tag $(Get-Date -Format s)" | Add-Content $st
    while ($null -eq (WorldExit $t)) { Start-Sleep 30 }
    if ((WorldExit $t) -ne 0) { "skip $t (world exit=$(WorldExit $t))" | Add-Content $st; continue }
    while (Test-Path $phone) { Start-Sleep 60 }
    if (-not $got) { pwsh scripts/unity-slot.ps1 -Acquire -Pool unity -Owner $Owner | Out-Null; $got = $true; "unity slot $(Get-Date -Format s)" | Add-Content $st }
    if (Step "import-$t-$Tag" { pwsh scripts/import-region.ps1 -Region $t }) {
      Beat unity
      Step "vqa-low-$t-$Tag" { pwsh scripts/visual-qa.ps1 -Scene "World_$t" -Tier Low -Lighting clear -Width 1920 -Height 1080 -OutputDir "$A/vqa/$Tag/$t/Low" } | Out-Null
      Step "vqa-high-$t-$Tag" { pwsh scripts/visual-qa.ps1 -Scene "World_$t" -Tier High -Lighting clear -Width 1920 -Height 1080 -OutputDir "$A/vqa/$Tag/$t/High" } | Out-Null
    }
    Beat unity
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
  }
  if ($got) { pwsh scripts/unity-slot.ps1 -Release -Pool unity -Owner $Owner | Out-Null }
  "UNITY DONE $Tag $($Tiles -join ',') $(Get-Date -Format s)" | Add-Content $st
}
else {
  while (-not ((Test-Path $wst) -and (Select-String -Path $wst -Pattern "^WORLD DONE $Tag " -Quiet))) { Start-Sleep 60 }
  pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner "$Owner-final" | Out-Null
  foreach ($t in $Tiles) {
    Step "route-$t-$Tag" { uv run --project tools/worldgen python scripts/export-route.py --region $t } | Out-Null
  }
  git status --short -- Data game/Assets *> "$L/final-route-diff-$Tag.txt"
  Step "catalog-check-$Tag" { uv run --project tools/worldgen python scripts/export-region-catalog.py --check } | Out-Null
  Step "pytest-gis-$Tag" { uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider } | Out-Null
  pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner "$Owner-final" | Out-Null
  # EditMode needs the project: wait for the unity chain of this tag (one Unity process per project directory)
  $ust = "$L/regen-unity.status"
  while (-not ((Test-Path $ust) -and (Select-String -Path $ust -Pattern "^UNITY DONE $Tag " -Quiet))) { Start-Sleep 60 }
  while (Test-Path $phone) { Start-Sleep 60 }
  pwsh scripts/unity-slot.ps1 -Acquire -Pool unity -Owner "$Owner-final" | Out-Null
  Step "editmode-$Tag" { pwsh scripts/test.ps1 -Platform EditMode } | Out-Null
  pwsh scripts/unity-slot.ps1 -Release -Pool unity -Owner "$Owner-final" | Out-Null
  git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
  "FINAL DONE $Tag $(Get-Date -Format s)" | Add-Content $st
}
