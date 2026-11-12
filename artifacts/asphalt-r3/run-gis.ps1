param([string]$Label = 'candidate-final', [switch]$EndOfRound)
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if (-not $EndOfRound) { throw 'Full GIS is permitted only at the end of a round; pass -EndOfRound.' }
$slotScript = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$heavyOwner = (& git branch --show-current).Trim()
if ($LASTEXITCODE -ne 0 -or -not $heavyOwner) { throw 'Cannot determine heavy-slot branch owner' }
# Call only after the world producer has exited. The session fixture in test_world_roads.py rewrites metadata.
$snapshot = Join-Path $PSScriptRoot "$Label-before-gis-$(Get-Date -Format yyyyMMdd-HHmmssfff)"
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
    & pwsh $slotScript -Acquire -Pool heavy -Owner $heavyOwner -PollSeconds 5
    if ($LASTEXITCODE -ne 0) { throw 'Heavy slot acquisition failed' }
    try {
        & uv run --project tools/worldgen python -m pytest tests/gis -q --junitxml "artifacts/asphalt-r3/$Label-gis.xml" *> "artifacts/asphalt-r3/$Label-gis.log"
        $testExit = $LASTEXITCODE
    } finally {
        & pwsh $slotScript -Release -Pool heavy -Owner $heavyOwner
    }
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
& uv run --project tools/worldgen python artifacts/asphalt-r3/audit_manifest.py > "artifacts/asphalt-r3/$Label-post-gis-manifest-audit.log"
$auditExit = $LASTEXITCODE
Add-Content artifacts/asphalt-r3/STATUS.md "$(Get-Date -Format o): GIS $Label exit=$testExit; przywrócono metadane producenta; audyt po testach exit=$auditExit. Wynik i błędy w $Label-gis.xml/log."
git add -f artifacts/asphalt-r3/STATUS.md
git commit -m "wip(asphalt): checkpoint GIS $Label and restored producer metadata"
if ($auditExit -ne 0) { exit $auditExit }
exit $testExit
