param([Parameter(Mandatory)][int]$PreparationPid)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
while(-not(Test-Path "$PSScriptRoot/baseline-preparation-receipt.json")){
    if(-not(Get-Process -Id $PreparationPid -ErrorAction SilentlyContinue)){throw 'Preparation stopped without receipt; inspect its log, do not import'}
    Start-Sleep -Seconds 5
}
$r=Get-Content "$PSScriptRoot/baseline-preparation-receipt.json" -Raw|ConvertFrom-Json
if($r.materials_exit_code -ne 0 -or $r.world_exit_code -ne 0){throw 'Preparation failed'}
& pwsh -File "$PSScriptRoot/import-baseline.ps1"
if($LASTEXITCODE -ne 0){throw 'Baseline import/captures failed'}
if(-not(Test-Path "$PSScriptRoot/Before.complete")){throw 'Complete Before marker missing'}
$out=Join-Path $PSScriptRoot 'before-source'
New-Item -ItemType Directory -Force $out|Out-Null
Copy-Item game/Assets/_Generated/World/bialystok-industrial-c/Meshes/world_edge.asset "$out/world_edge.asset"
Copy-Item game/Assets/_Generated/World/bialystok-industrial-c/Meshes/Low/world_edge_far.asset "$out/world_edge_far-Low.asset"
Copy-Item game/Assets/_Generated/World/bialystok-industrial-c/Meshes/High/world_edge_far.asset "$out/world_edge_far-High.asset"
foreach($name in @('far_field.glb','far_field.low.glb','far_field_apron.json','far_field_gis_cache.json')){
    Copy-Item "Data/raw/derived/bialystok-industrial-c/world/$name" (Join-Path $out $name)
}
Copy-Item Data/Regions/bialystok-industrial-c/generated/far_field_qa.json "$PSScriptRoot/before-far-field-qa.json"
$files=Get-ChildItem $out -File
$index=foreach($f in $files){@{name=$f.Name;bytes=$f.Length;sha256=(Get-FileHash $f.FullName -Algorithm SHA256).Hash}}
$index|ConvertTo-Json|Set-Content "$PSScriptRoot/before-source-sha.json"
Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Pełne Before i native ukończone; siatki apron/far, źródłowe GLB i profil zamrożone z SHA. Następnie maski apron i diagnoza styku kurtyn; kod produkcyjny r6 jeszcze bez zmiany."
git add -f artifacts/edge-r6/STATUS.md artifacts/edge-r6/before-source-sha.json
git commit -m 'WIP edge r6: freeze complete merged-main baseline before apron or curtain edits'
if($LASTEXITCODE -ne 0){throw 'Baseline checkpoint failed'}
(Get-Date -Format o)|Set-Content "$PSScriptRoot/Baseline.ready"
