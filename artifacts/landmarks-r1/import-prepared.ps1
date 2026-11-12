# Import only prepared data. Heavy generators run separately under -Pool heavy.
$ErrorActionPreference = 'Stop'
$wt = Split-Path (Split-Path $PSScriptRoot)
Set-Location $wt
. "$wt/scripts/env.ps1"
$region = 'bialystok-industrial-c'
$spec = Get-Content "$wt/art-source/world/materials/materials_spec.json" -Raw | ConvertFrom-Json
foreach ($entry in $spec.sets.PSObject.Properties) {
    $maps = $entry.Value.files.Medium
    if (-not $maps) { continue }
    foreach ($name in $maps.files) {
        if (-not (Test-Path "$wt/art-source/world/materials/$($maps.dir)/$name")) {
            throw "Prepared PBR map missing: $($entry.Name)/$name; run a heavy preparation step first"
        }
    }
}
if (-not (Test-Path "$wt/Data/raw/derived/$region/world/chunk_0_0.glb")) {
    throw 'Prepared world chunks missing; run the heavy World step first'
}
$log = Join-Path $LogsDir "landmarks-import-$region-$(Get-Timestamp).log"
$code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.World.Import.RegionImporter.ImportBatch',
    '-region',$region,'-tiers','Low,High','-materialTier','Medium')
$result = Select-String -Path $log -Pattern 'IMPORT_RESULT:.*' | Select-Object -Last 1
if ($code -ne 0 -or -not $result -or $result.Line -notmatch 'IMPORT_RESULT: OK') {
    Show-UnityLogErrors $log
    throw "Prepared import failed ($code), log: $log"
}
Write-Host $result.Line
Write-Host "log: $log"
