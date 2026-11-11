$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
$manifest='Data/Regions/bialystok-industrial-c/generated/world_manifest.json'
$snapshot='artifacts/life-r1/manifest-before-gis.json'
Copy-Item $manifest $snapshot
$before=(Get-FileHash $manifest -Algorithm SHA256).Hash
& uv run --project tools/worldgen python -m pytest tests/gis -q *> artifacts/life-r1/gis.log
$testCode=$LASTEXITCODE
$after=(Get-FileHash $manifest -Algorithm SHA256).Hash
$restored=$false
if($before -ne $after) { Copy-Item $snapshot $manifest; $restored=$true }
@{exit_code=$testCode;manifest_before=$before;manifest_after=$after;manifest_restored=$restored} | ConvertTo-Json | Set-Content artifacts/life-r1/gis-result.json
if($testCode -ne 0){throw "GIS failed ($testCode)"}
