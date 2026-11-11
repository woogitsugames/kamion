param([string]$Label = 'candidate-final')
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
# Call only after the world producer has exited. The session fixture in test_world_roads.py rewrites metadata.
$snapshot = Join-Path $PSScriptRoot "$Label-before-gis"
$paths = @('Data/Regions/bialystok-industrial-c/generated',
    'Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json',
    'art-source/world/props/props_meta.json')
foreach ($rel in $paths) {
    $target = Join-Path $snapshot $rel
    New-Item -ItemType Directory -Force (Split-Path $target) | Out-Null
    Copy-Item -LiteralPath $rel -Destination $target -Recurse -Force
}
$testExit = 1
try {
    & uv run --project tools/worldgen python -m pytest tests/gis -q --junitxml "artifacts/asphalt-r1/$Label-gis.xml" *> "artifacts/asphalt-r1/$Label-gis.log"
    $testExit = $LASTEXITCODE
} finally {
    # Restore the producer's byte-exact metadata, not the test fixture's side effects.
    foreach ($rel in $paths) {
        $source = Join-Path $snapshot $rel
        if (Test-Path $source -PathType Container) {
            Copy-Item "$source/*" -Destination $rel -Recurse -Force
        } else {
            Copy-Item -LiteralPath $source -Destination $rel -Force
        }
    }
}
& uv run --project tools/worldgen python artifacts/asphalt-r1/audit_manifest.py > "artifacts/asphalt-r1/$Label-post-gis-manifest-audit.log"
$auditExit = $LASTEXITCODE
Add-Content artifacts/asphalt-r1/STATUS.md "$(Get-Date -Format o): GIS $Label exit=$testExit; przywrócono metadane producenta; audyt po testach exit=$auditExit. Wynik i błędy w $Label-gis.xml/log."
git add -f artifacts/asphalt-r1/STATUS.md
git commit -m "wip(asphalt): checkpoint GIS $Label and restored producer metadata"
if ($auditExit -ne 0) { exit $auditExit }
exit $testExit
