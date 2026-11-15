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
  "$name start $(Get-Date -Format s)" | Add-Content $st
  & $b *> "$L/$name.log"
  "$name exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
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
    while (-not (Select-String -Path $wst -Pattern "^world-$t-$Tag exit=" -Quiet -ErrorAction SilentlyContinue)) { Start-Sleep 30 }
    if (-not (Select-String -Path $wst -Pattern "^world-$t-$Tag exit=0 " -Quiet)) { "skip $t (world failed)" | Add-Content $st; continue }
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
