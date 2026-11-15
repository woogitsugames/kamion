# fix-pr80-s21: rebuild roads.graph.json of dk65-05 (graph_filter) + write the construction_site override
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$L = 'artifacts/verify-cloud-c/logs'; $st = "$L/region05.status"
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner verify-cloud-c | Out-Null
"region start $(Get-Date -Format s)" | Add-Content $st
uv run --project tools/worldgen tools/worldgen/build_region.py --region dk65-05 *> "$L/region-dk65-05.log"
"region exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
if ($LASTEXITCODE -eq 0) {
  uv run --project tools/worldgen python tools/worldgen/qa/construction_sites.py --region dk65-05 --ways 1151531612,1151531613,1151531608 *> "$L/sites-dk65-05.log"
  "sites exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
}
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner verify-cloud-c | Out-Null
"STAGE DONE region05 $(Get-Date -Format s)" | Add-Content $st
