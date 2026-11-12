$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-edge-r5'){throw 'Wrong round'}
if(-not(Test-Path "$PSScriptRoot/Gis.finished")){throw 'Wait for complete final GIS and integrity check'}
$integrity=Get-Content "$PSScriptRoot/post-gis-own-integrity.json" -Raw|ConvertFrom-Json
if(-not$integrity.all_own_outputs_unchanged){throw 'Rendered own outputs changed during GIS'}
foreach($p in $integrity.after.PSObject.Properties){
    if((Get-FileHash -LiteralPath $p.Name -Algorithm SHA256).Hash -ne $p.Value){throw "Own output changed after final GIS: $($p.Name)"}
}
$xml=[xml](Get-Content "$PSScriptRoot/tests/gis-final.xml" -Raw)
$suites=@($xml.SelectNodes('//testsuite'))
$failures=@($xml.SelectNodes('//testcase[failure or error]')|ForEach-Object {"$($_.classname)::$($_.name)"})
$summary=@{pytest_exit_code=$integrity.pytest_exit_code;
    tests=($suites|Measure-Object tests -Sum).Sum;
    failures=($suites|Measure-Object failures -Sum).Sum;
    errors=($suites|Measure-Object errors -Sum).Sum;
    skipped_or_xfailed=($suites|Measure-Object skipped -Sum).Sum;
    failed_cases=$failures;note='Original full GIS result; scope cleanup never changes it into PASS.'}
$summary|ConvertTo-Json -Depth 5|Set-Content "$PSScriptRoot/gis-result.json"
# Only JSON metadata and two short hashes; no geometry regeneration or heavy
# Python task. The full test already released its heavy lease in finally.
& uv run --project tools/worldgen python "$PSScriptRoot/scope_generated.py" *> "$PSScriptRoot/scope-generated.log"
if($LASTEXITCODE -ne0){throw 'Generated scope cleanup failed'}
foreach($p in $integrity.after.PSObject.Properties){
    if((Get-FileHash -LiteralPath $p.Name -Algorithm SHA256).Hash -ne $p.Value){throw "Scope cleanup changed rendered own output: $($p.Name)"}
}
$allowed=@('Data/Regions/bialystok-industrial-c/generated/far_field_qa.json',
    'Data/Regions/bialystok-industrial-c/generated/world_manifest.json',
    'Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json')
$changed=@(git diff --name-only)
foreach($path in $changed){if($path -notin $allowed){throw "Unexpected remaining tracked modification: $path"}}
git diff --check -- @allowed
if($LASTEXITCODE -ne0){throw 'Generated scope whitespace check failed'}
@{own_files_verified=$integrity.after;retained_world_manifest_fields=@('far_field','materials.far_field_buildings');
  original_pytest_exit_code=$integrity.pytest_exit_code;remaining_generated_changes=$changed;
  verification='Rendered After SHA, post-test SHA and post-scope SHA match for all six own outputs';
  finished=(Get-Date -Format o)}|ConvertTo-Json -Depth 6|Set-Content "$PSScriptRoot/post-gis-scope.json"
Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Po pełnym GIS zweryfikowano sześć własnych SHA względem renderów After, zachowano własne pola far-field świeżego manifestu i odtworzono obce generated/props. Pozostałe zmiany tracked ograniczają się do trzech własnych manifestów. Oryginalny wynik GIS w gis-result.json i logu; scope nie zmienia jego oceny."
git add -- @allowed
git add -f artifacts/edge-r5/STATUS.md artifacts/edge-r5/gis-result.json artifacts/edge-r5/generated-scope.json artifacts/edge-r5/post-gis-scope.json artifacts/edge-r5/tests/gis-final.xml
git commit -m 'WIP edge r5: preserve verified edge outputs and restore unrelated generated metadata'
if($LASTEXITCODE -ne0){throw 'Post-GIS checkpoint failed'}
(Get-Date -Format o)|Set-Content "$PSScriptRoot/post-gis.complete"
Get-Content "$PSScriptRoot/gis-result.json"
