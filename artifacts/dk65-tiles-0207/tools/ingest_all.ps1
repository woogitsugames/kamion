# ADR 0207: ingest + build_region for dk65-02..05 (sequential). Status: logs/ingest.status
param([string[]]$Tiles = @('dk65-02','dk65-03','dk65-04','dk65-05'))
$ErrorActionPreference = 'Continue'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$L = 'artifacts/dk65-tiles-0207/logs'; $st = "$L/ingest.status"
foreach ($t in $Tiles) {
  "$t ingest start $(Get-Date -Format s)" | Add-Content $st
  uv run --project tools/worldgen tools/worldgen/ingest.py --region $t *> "$L/ingest-$t.log"
  "$t ingest exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
  uv run --project tools/worldgen tools/worldgen/build_region.py --region $t *> "$L/build_region-$t.log"
  "$t build_region exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
}
"INGEST DONE $(Get-Date -Format s)" | Add-Content $st
