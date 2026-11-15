# verify-cloud-c (s21): staged chain. -Stage dk65 | cworld | cunity | cbase | editmode | pytest | fid
# Status: artifacts/verify-cloud-c/logs/<stage>.status  (one line per step start / exit, "STAGE DONE" at the end)
param([Parameter(Mandatory)][string]$Stage, [string]$Tiles = 'dk65-05,dk65-06,dk65-02,dk65-03,dk65-04')
$ErrorActionPreference = 'Continue'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$A = 'artifacts/verify-cloud-c'; $L = "$A/logs"; $st = "$L/$Stage.status"; $o = "verify-cloud-c-$Stage"
$T = $Tiles -split ','
$phone = 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN'
$putry = 'putry_above,route_putry_approach,driver_andersa_to_putry,ortho_putry,g3b_eye_s1582,g3b_eye_s1632'
function Step($name, $pool, [scriptblock]$b) {
  if ($pool -eq 'unity') { while (Test-Path $phone) { Start-Sleep 60 } }
  pwsh scripts/unity-slot.ps1 -Acquire -Pool $pool -Owner $o | Out-Null
  "$name start $(Get-Date -Format s)" | Add-Content $st
  $global:LASTEXITCODE = 0
  & $b *> "$L/$name.log"
  $code = $LASTEXITCODE
  "$name exit=$code $(Get-Date -Format s)" | Add-Content $st
  pwsh scripts/unity-slot.ps1 -Release -Pool $pool -Owner $o | Out-Null
  if ($pool -eq 'unity') {
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
    if ((Test-Path game/Assets/Resources) -and -not (Get-ChildItem game/Assets/Resources -Force)) { Remove-Item game/Assets/Resources, game/Assets/Resources.meta -Force -ErrorAction SilentlyContinue }
  }
  return ($code -eq 0)
}
function Vqa($tier, $dir) {
  pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting overcast -Width 1920 -Height 1080 -Cameras $putry -Gate3 Data/Regions/bialystok-industrial-c/gate3_cameras.json -OutputDir $dir
}
$C = 'bialystok-industrial-c'
switch ($Stage) {
  'dk65' {
    foreach ($t in $T) {
      $ok = Step "world-$t" heavy {
        uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $t --context
        if ($LASTEXITCODE -eq 0) { uv run --project tools/worldgen python scripts/export-route.py --region $t }
      }
      if (-not $ok) { "SKIP import/vqa $t (world failed)" | Add-Content $st; continue }
      $ok = Step "import-$t" unity { pwsh scripts/import-region.ps1 -Region $t }
      if (-not $ok) { "SKIP vqa $t (import failed)" | Add-Content $st; continue }
      Step "vqa-low-$t" unity { pwsh scripts/visual-qa.ps1 -Scene "World_$t" -Tier Low -Lighting clear -Width 1920 -Height 1080 -OutputDir "$A/pr80/$t/Low-clear" } | Out-Null
    }
  }
  'fid' {
    foreach ($t in $T) {
      Step "fidelity-$t" heavy { uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region $t --no-tile --art "$A/pr80/fidelity/$t" } | Out-Null
    }
  }
  'cbase' {
    Step 'cbase-vqa-low' unity { Vqa Low "$A/pr82/base/Low-overcast" } | Out-Null
    Step 'cbase-vqa-high' unity { Vqa High "$A/pr82/base/High-overcast" } | Out-Null
  }
  'cworld' {
    $ok = Step 'c-world' heavy {
      uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $C
      if ($LASTEXITCODE -eq 0) { uv run --project tools/worldgen python scripts/export-route.py --region $C }
    }
    if ($ok) {
      Step 'c-piers' heavy { uv run --project tools/worldgen python tools/worldgen/qa/check_piers_vs_roads.py --region $C --out "$A/pr82/piers_vs_roads.json" } | Out-Null
    }
  }
  'cunity' {
    $ok = Step 'c-import' unity { pwsh scripts/import-region.ps1 -Region $C }
    if ($ok) {
      Step 'c-vqa-low' unity { Vqa Low "$A/pr82/after/Low-overcast" } | Out-Null
      Step 'c-vqa-high' unity { Vqa High "$A/pr82/after/High-overcast" } | Out-Null
    }
  }
  'editmode' {
    Step 'editmode' unity { pwsh scripts/test.ps1 -Platform EditMode } | Out-Null
  }
  'pytest' {
    Step 'pytest-gis' heavy { uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider } | Out-Null
  }
}
"STAGE DONE $Stage $(Get-Date -Format s)" | Add-Content $st
