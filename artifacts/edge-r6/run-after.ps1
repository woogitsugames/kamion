$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-edge-r6'){throw 'Wrong round'}
if(-not(Test-Path "$PSScriptRoot/apron-green-result.json")){throw 'Green stopped without a verified result; inspect its log'}
$green=Get-Content "$PSScriptRoot/apron-green-result.json" -Raw|ConvertFrom-Json
if(-not$green.expected_result_verified -or $green.failed -ne0 -or $green.passed -ne16 -or
   $green.source_sha256 -ne (Get-FileHash game/Assets/_Project/World/Import/WorldEdgeBuilder.cs -Algorithm SHA256).Hash){throw 'Verified Green for current source required'}
foreach($property in $green.test_sha256.PSObject.Properties){
    if((Get-FileHash -LiteralPath $property.Name -Algorithm SHA256).Hash -ne $property.Value){throw 'Regression tests changed since Green'}
}
if(Test-Path "$PSScriptRoot/After.ready"){throw 'After evidence already frozen; preserve before a deliberate new attempt'}
& pwsh -File "$PSScriptRoot/heavy.ps1" -Task BuildWorld *> "$PSScriptRoot/build-world-after.log"
if($LASTEXITCODE -ne0){throw 'Post-change full world generation failed'}
if(Select-String -LiteralPath "$PSScriptRoot/build-world-after.log" -SimpleMatch 'fallback=True' -Quiet){throw 'Megascans fallback in post-change world'}
$out=Join-Path $PSScriptRoot 'after-source'
New-Item -ItemType Directory -Force $out|Out-Null
foreach($name in @('far_field.glb','far_field.low.glb','far_field_apron.json','far_field_gis_cache.json')){
    Copy-Item "Data/raw/derived/bialystok-industrial-c/world/$name" (Join-Path $out $name)
}
Copy-Item Data/Regions/bialystok-industrial-c/generated/far_field_qa.json "$PSScriptRoot/after-far-field-qa.json"
Copy-Item Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json "$PSScriptRoot/after-far-field-source-manifest.json"
Copy-Item Data/Regions/bialystok-industrial-c/generated/world_manifest.json "$PSScriptRoot/after-operational-world-manifest.json"
Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Po Green wykonano wymagany pełny build_world pod heavy bez fallback=True. Surowe GLB/profile/cache oraz QA i manifest After zachowane. Następnie przebudowa edge i obie macierze renderów, bez pełnego GIS przed oceną obrazu."
git add -f artifacts/edge-r6/STATUS.md
git commit -m 'WIP edge r5: regenerate full world after apron transition change'
if($LASTEXITCODE -ne0){throw 'Post-generator checkpoint failed'}
& pwsh -File "$PSScriptRoot/validate.ps1" -Phase After
if($LASTEXITCODE -ne0){throw 'After rebuild or capture failed; inspect logs before resuming'}
Copy-Item game/Assets/_Generated/World/bialystok-industrial-c/Meshes/world_edge.asset "$out/world_edge.asset"
Copy-Item game/Assets/_Generated/World/bialystok-industrial-c/Meshes/Low/world_edge_far.asset "$out/world_edge_far-Low.asset"
Copy-Item game/Assets/_Generated/World/bialystok-industrial-c/Meshes/High/world_edge_far.asset "$out/world_edge_far-High.asset"
$files=Get-ChildItem $out -File
$hashes=foreach($file in $files){@{name=$file.Name;bytes=$file.Length;sha256=(Get-FileHash $file.FullName -Algorithm SHA256).Hash}}
$hashes|ConvertTo-Json|Set-Content "$PSScriptRoot/after-source-sha.json"
Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) After ukończone: obrazy telefonu i native oraz rzeczywiste siatki Unity zamrożone z SHA. Wynik wizualny i wszystkie budżety wymagają oceny; nie ogłaszamy jeszcze PASS."
git add -f artifacts/edge-r6/STATUS.md artifacts/edge-r6/after-source-sha.json
git commit -m 'WIP edge r5: freeze complete generated and imported After evidence'
if($LASTEXITCODE -ne0){throw 'After evidence checkpoint failed'}
(Get-Date -Format o)|Set-Content "$PSScriptRoot/After.ready"
