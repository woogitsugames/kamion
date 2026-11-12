$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $root
while(-not(Test-Path "$PSScriptRoot/gis-final-receipt.json")){Start-Sleep -Seconds 2}
$receipt=Get-Content "$PSScriptRoot/gis-final-receipt.json" -Raw|ConvertFrom-Json
$manifestPath='Data/Regions/bialystok-industrial-c/generated/world_manifest.json'
Copy-Item $manifestPath "$PSScriptRoot/world-manifest-after-gis.json"
$manifest=Get-Content $manifestPath -Raw|ConvertFrom-Json
$cli=Get-Content "$PSScriptRoot/cli-chunks-before-gis.json" -Raw|ConvertFrom-Json
$rows=foreach($chunk in $manifest.chunks){
    $old=$cli|Where-Object id -eq $chunk.id
    if(@($old).Count -ne 1){throw 'Missing frozen CLI chunk'}
    $path=$chunk.file
    if(-not[IO.Path]::IsPathRooted($path)){$path=Join-Path $root $path}
    $actual=if(Test-Path -LiteralPath $path){(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}else{$null}
    [PSCustomObject]@{id=$chunk.id;cli_sha256=$old.sha256;regenerated_sha256=$chunk.sha256;
        actual_file=$path;actual_sha256=$actual;cli_matches_regenerated=($old.sha256 -eq $chunk.sha256);
        actual_matches_regenerated=($actual -eq $chunk.sha256);
        independent_pytest_path=($path -match '[\\/]pytest-of-matma[\\/]pytest-\d+[\\/]')}
}
$rows|ConvertTo-Json -Depth 5|Set-Content "$PSScriptRoot/chunk-manifest-drift.json"
if(@($rows).Count -ne 64){throw 'Expected 64 chunk records'}
$checks=@{}
foreach($pair in @(
    @('Data/Regions/bialystok-industrial-c/generated/far_field_qa.json','pre-final-gis-far-field-qa.json'),
    @('Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json','pre-final-gis-source-manifest.json'))){
    $checks[$pair[0]]=(Get-FileHash -LiteralPath $pair[0] -Algorithm SHA256).Hash -eq (Get-FileHash -LiteralPath "$PSScriptRoot/$($pair[1])" -Algorithm SHA256).Hash
}
foreach($name in @('far_field.glb','far_field.low.glb')){
    $p="Data/raw/derived/bialystok-industrial-c/world/$name"
    $checks[$p]=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -eq (Get-FileHash -LiteralPath "$PSScriptRoot/before-source/$name" -Algorithm SHA256).Hash
}
if(@($checks.Values|Where-Object {-not $_}).Count){throw 'Own far-field output changed during GIS; do not restore blindly'}
$base=(git show "HEAD:$manifestPath") -join "`n"|ConvertFrom-Json
$fresh=Get-Content "$PSScriptRoot/regenerated-world-manifest.json" -Raw|ConvertFrom-Json
if(($base.far_field|ConvertTo-Json -Depth 30 -Compress) -ne ($fresh.far_field|ConvertTo-Json -Depth 30 -Compress)){throw 'Own far field needs preservation'}
if(($base.materials.far_field_buildings|ConvertTo-Json -Depth 30 -Compress) -ne ($fresh.materials.far_field_buildings|ConvertTo-Json -Depth 30 -Compress)){throw 'Own far material needs preservation'}
git restore -- $manifestPath Data/Regions/bialystok-industrial-c/generated/landmarks/viaduct_putry_underdeck.spec.json Data/Regions/bialystok-industrial-c/generated/roads_qa.json Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json art-source/world/props/props_meta.json art-source/world/props/street_props.glb
if($LASTEXITCODE -ne 0){throw 'Generated scope restore failed'}
@{own_far_output_unchanged=$checks;world_manifest_far_fields_equal_to_base=$true;gis_exit_code=$receipt.exit_code;
    cli_vs_regenerated_matches=@($rows|Where-Object cli_matches_regenerated).Count;
    actual_vs_regenerated_matches=@($rows|Where-Object actual_matches_regenerated).Count;
    independent_pytest_paths=@($rows|Where-Object independent_pytest_path).Count;
    note='This scope restore does not change a failing GIS test into a pass. All original logs are retained.';
    finished=(Get-Date -Format o)}|ConvertTo-Json -Depth 6|Set-Content "$PSScriptRoot/post-gis-scope.json"
Add-Content "$PSScriptRoot/STATUS.md" 'Krok 15: końcowy GIS zakończony; oryginalny kod wyjścia i log zachowano. Audyt SHA własnych obu GLB, QA i źródłowego manifestu chronił odtworzenie cudzych metadanych. Własne pola world_manifest są zgodne z bazą r3, więc przywrócono plik bez zmiany danych edge. Szczegóły testów wymagają odczytu przed REPORT.'
git add -f artifacts/edge-r4/STATUS.md artifacts/edge-r4/post-gis-scope.json artifacts/edge-r4/chunk-manifest-drift.json
git commit -m 'WIP edge r3: audit final GIS output and restore unrelated generated metadata'
if($LASTEXITCODE -ne 0){throw 'Post-GIS checkpoint failed'}
(Get-Date -Format o)|Set-Content "$PSScriptRoot/post-gis.complete"
