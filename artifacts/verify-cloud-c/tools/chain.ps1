# verify-cloud-c: staged chain. -Stage dk65 | cbase | c | pytest. Status: artifacts/verify-cloud-c/logs/<stage>.status
param([Parameter(Mandatory)][string]$Stage, [string[]]$Tiles = @('dk65-02','dk65-03','dk65-04','dk65-05'))
$ErrorActionPreference = 'Continue'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$A = 'artifacts/verify-cloud-c'; $L = "$A/logs"; $st = "$L/$Stage.status"; $o = 'verify-cloud-c'
$phone = 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN'
$putry = 'putry_above,route_putry_approach,driver_andersa_to_putry,ortho_putry,g3b_eye_s1582,g3b_eye_s1632'
function Step($name, $pool, [scriptblock]$b) {
  if ($pool -eq 'unity') { while (Test-Path $phone) { Start-Sleep 60 } }
  pwsh scripts/unity-slot.ps1 -Acquire -Pool $pool -Owner $o | Out-Null
  "$name start $(Get-Date -Format s)" | Add-Content $st
  & $b *> "$L/$name.log"
  "$name exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
  pwsh scripts/unity-slot.ps1 -Release -Pool $pool -Owner $o | Out-Null
  if ($pool -eq 'unity') { git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null }
}
function Vqa($tier, $dir) {
  pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting overcast -Width 1920 -Height 1080 -Cameras $putry -Gate3 Data/Regions/bialystok-industrial-c/gate3_cameras.json -OutputDir $dir
}
$C = 'bialystok-industrial-c'
switch ($Stage) {
  'dk65' {
    foreach ($t in $Tiles) {
      Step "world-$t" heavy {
        uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $t --context
        if ($LASTEXITCODE -eq 0) { uv run --project tools/worldgen python scripts/export-route.py --region $t }
      }
      Step "import-$t" unity { pwsh scripts/import-region.ps1 -Region $t }
      Step "vqa-low-$t" unity { pwsh scripts/visual-qa.ps1 -Scene "World_$t" -Tier Low -Lighting clear -Width 1920 -Height 1080 -OutputDir "$A/pr80/$t/Low-clear" }
    }
    foreach ($t in $Tiles) {
      Step "fidelity-$t" heavy { uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region $t --no-tile --art "$A/pr80/fidelity/$t" }
    }
  }
  'cbase' {
    Step 'cbase-vqa-low' unity { Vqa Low "$A/pr82/base/Low-overcast" }
    Step 'cbase-vqa-high' unity { Vqa High "$A/pr82/base/High-overcast" }
  }
  'c' {
    Step 'c-world' heavy {
      uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $C
      if ($LASTEXITCODE -eq 0) { uv run --project tools/worldgen python scripts/export-route.py --region $C }
    }
    Step 'c-piers' heavy { uv run --project tools/worldgen python tools/worldgen/qa/check_piers_vs_roads.py --region $C --out "$A/pr82/piers_vs_roads.json" }
    Step 'c-fidelity' heavy { uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region $C --art "$A/pr82/fidelity" }
    Step 'c-import' unity { pwsh scripts/import-region.ps1 -Region $C }
    Step 'c-vqa-low' unity { Vqa Low "$A/pr82/after/Low-overcast" }
    Step 'c-vqa-high' unity { Vqa High "$A/pr82/after/High-overcast" }
  }
  'pytest' {
    Step 'pytest-gis' heavy { uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider }
  }
}
"STAGE DONE $Stage $(Get-Date -Format s)" | Add-Content $st
