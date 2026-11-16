# int-dk65-s22: world chain (heavy slot, build_world per tile, commit+push generated per tile) or unity chain
# (unity slot; per tile waits for its world step, then import + visual-qa Low/High). No export-route (route_start is
# owned by spawn-fix-0262). Status: logs/chain-<Mode>.status ; end marker "<MODE> DONE".
param([string[]]$Tiles, [ValidateSet('world', 'unity')][string]$Mode = 'world', [string]$Tag = 'r1', [string]$Owner = 'int-dk65-s22')
$ErrorActionPreference = 'Continue'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$A = 'artifacts/int-dk65-s22'; $L = "$A/logs"; $st = "$L/chain-$Mode.status"; $wst = "$L/chain-world.status"
$main = 'C:\Users\matma\Documents\Claude\kamion'
$phone = "$main\artifacts\locks\PHONE_RUN"
function Step($name, [scriptblock]$b) {
  # exit -1073741502 (0xC0000142) = the process did not start (desktop heap / DLL init): retry, up to 3 runs
  foreach ($try in 1..3) {
    "$name start $(Get-Date -Format s)" | Add-Content $st
    $global:LASTEXITCODE = 0
    & $b *> "$L/$name.log"
    $code = $LASTEXITCODE
    "$name exit=$code $(Get-Date -Format s)" | Add-Content $st
    if ($code -ne -1073741502) { break }
    Copy-Item "$L/$name.log" "$L/$name.try$try.log" -Force; Start-Sleep 20
  }
}
# last recorded exit code of a world step, $null while it has not finished. s22 "wait bug": Select-String on a status
# file that does not exist yet is a statement-terminating error - it ended the wait loop AND skipped the exit=0 guard,
# so the import started before build_world. Never read the file without Test-Path.
function WorldExit($t) {
  if (-not (Test-Path $wst)) { return $null }
  $m = @(Get-Content $wst -ErrorAction SilentlyContinue | Where-Object { $_ -match "^world-$t-$Tag exit=(-?\d+) " })
  if ($m.Count -eq 0) { return $null }
  [void]($m[-1] -match 'exit=(-?\d+) '); return [int]$Matches[1]
}
function Beat($pool) { $f = Get-Item "$main\artifacts\locks\$pool-slots\$Owner.slot" -ErrorAction SilentlyContinue; if ($f) { $f.LastWriteTime = Get-Date } }
$Tiles = @($Tiles | ForEach-Object { $_ -split "," } | Where-Object { $_ })
if ($Mode -eq 'world') {
  pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $Owner | Out-Null
  "heavy slot $(Get-Date -Format s)" | Add-Content $st
  foreach ($t in $Tiles) {
    Step "world-$t-$Tag" { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $t --context }
    Beat heavy
    if ((Get-Content $st -Tail 1) -match 'exit=0 ') {
      git add "Data/Regions/$t/generated" *>> "$L/git-$t.log"
      Get-ChildItem "Data/SourceManifests" -Filter "$t-*.json" -ErrorAction SilentlyContinue | ForEach-Object { git add $_.FullName *>> "$L/git-$t.log" }
      git commit -q -m "wip(int-dk65-s22): generated $t (0220 + 0218 + 0222, bez toru)`n`nCo-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>" *>> "$L/git-$t.log"
      git push -q *>> "$L/git-$t.log"
    }
  }
  pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner $Owner | Out-Null
  "WORLD DONE $Tag $($Tiles -join ',') $(Get-Date -Format s)" | Add-Content $st
}
else {
  $got = $false
  foreach ($t in $Tiles) {
    "wait world-$t-$Tag $(Get-Date -Format s)" | Add-Content $st
    while ($null -eq (WorldExit $t)) { Start-Sleep 30 }
    if ((WorldExit $t) -ne 0) { "skip $t (world exit=$(WorldExit $t))" | Add-Content $st; continue }
    while (Test-Path $phone) { Start-Sleep 60 }
    if (-not $got) { pwsh scripts/unity-slot.ps1 -Acquire -Pool unity -Owner $Owner | Out-Null; $got = $true; "unity slot $(Get-Date -Format s)" | Add-Content $st }
    Step "import-$t-$Tag" { pwsh scripts/import-region.ps1 -Region $t }
    Beat unity
    Step "vqa-low-$t-$Tag" { pwsh scripts/visual-qa.ps1 -Scene "World_$t" -Tier Low -Lighting clear -Width 1920 -Height 1080 -OutputDir "$A/$t/$Tag/Low-clear" }
    Step "vqa-high-$t-$Tag" { pwsh scripts/visual-qa.ps1 -Scene "World_$t" -Tier High -Lighting clear -Width 1920 -Height 1080 -OutputDir "$A/$t/$Tag/High-clear" }
    Beat unity
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
  }
  if ($got) { pwsh scripts/unity-slot.ps1 -Release -Pool unity -Owner $Owner | Out-Null }
  "UNITY DONE $Tag $($Tiles -join ',') $(Get-Date -Format s)" | Add-Content $st
}
