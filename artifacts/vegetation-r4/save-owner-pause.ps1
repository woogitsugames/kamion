$ErrorActionPreference='Stop'
$repo='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
Set-Location $repo
$round=Join-Path $repo 'artifacts/vegetation-r4'
$backup=Join-Path $round 'owner-pause-backup-20261112'
if (Test-Path -LiteralPath $backup) { throw 'Pause backup exists; inspect before repeating' }
$preserve=@(
 'Data/Regions/bialystok-industrial-c/generated/far_field_qa.json',
 'Data/Regions/bialystok-industrial-c/generated/landmarks/viaduct_putry_underdeck.spec.json',
 'Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json',
 'Data/Regions/bialystok-industrial-c/generated/world_manifest.json',
 'Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json',
 'art-source/world/props/props_meta.json',
 'art-source/world/props/street_props.glb',
 'Data/raw/derived/bialystok-industrial-c/world/chunk_6_6.glb',
 'Data/raw/derived/bialystok-industrial-c/world/chunk_6_6.low.glb'
)
$records=@(foreach($relative in $preserve) {
    $source=Join-Path $repo $relative
    $target=Join-Path $backup $relative
    New-Item -ItemType Directory -Force (Split-Path $target -Parent) | Out-Null
    $hash=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    Copy-Item -LiteralPath $source -Destination $target
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $hash -or
        (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $hash) { throw "Backup changed or mismatched: $relative" }
    [ordered]@{file=$relative; bytes=(Get-Item -LiteralPath $source).Length; sha256=$hash}
})
$result=[ordered]@{
    saved_at=(Get-Date -Format o)
    branch=(git branch --show-current).Trim()
    head_before_handoff=(git rev-parse HEAD).Trim()
    plantings_sha256=(Get-FileHash tools/worldgen/streetscape/plantings.py -Algorithm SHA256).Hash
    targeted_test_sha256=(Get-FileHash tests/gis/test_berberis_0109_rings.py -Algorithm SHA256).Hash
    ground_fixture_sha256=(Get-FileHash tests/gis/fixtures/berberis_0109_ground_c.json -Algorithm SHA256).Hash
    backup_root=$backup
    preserved=$records
    note='Seven dirty generator-side-effect files plus two current C GLBs copied and SHA-verified. Originals unchanged, no jobs terminated. Binary backups stay in artifacts, not staged into Git.'
}
$result | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 artifacts/vegetation-r4/OWNER-PAUSE-SNAPSHOT.json
$result | ConvertTo-Json -Depth 3
