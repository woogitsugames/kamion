$ErrorActionPreference='Stop'
$source=(Resolve-Path $PSScriptRoot).Path
$root=(Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $root
if((Split-Path $source -Leaf) -ne 'edge-r5' -or (git branch --show-current).Trim() -ne 'gpt-edge-r5'){throw 'Wrong round'}
if(-not(Test-Path "$source/post-gis.complete")){throw 'Post-GIS checks not complete'}
if(-not(Test-Path "$source/gis-final-receipt.json")){throw 'Missing final GIS result'}
if(-not(Test-Path "$source/REPORT.md") -or @(Get-Content "$source/REPORT.md").Count -gt20){throw 'Missing/oversized report'}
$target='C:/Users/matma/Documents/Claude/kamion/artifacts/edge-r5'
$log=Join-Path $root 'artifacts/edge-r5-delivery.log'
$reportCommit=(git rev-parse HEAD).Trim()
& robocopy $source $target /E /XJ /MT:1 /R:1 /W:1 /XF REPORT.md delivery-receipt.json /NFL /NDL /NP "/LOG:$log"
$copyCode=$LASTEXITCODE
if($copyCode -ge8){throw "Robocopy failed: $copyCode"}
Copy-Item -LiteralPath $log -Destination "$source/robocopy-delivery.log"
Copy-Item -LiteralPath $log -Destination "$target/robocopy-delivery.log"
Add-Content "$source/STATUS.md" "$(Get-Date -Format o) Pełny robocopy r5 zakończony. REPORT opublikowany po dowodach. Weryfikacja obejmuje każdy względny plik i rozmiar oraz SHA kluczowych plików; liczby w delivery-receipt.json. Bez commitowania do main, push i merge do main. Następny krok: gałąź r6 i merge main do niej."
Copy-Item -LiteralPath "$source/STATUS.md" -Destination "$target/STATUS.md"
Copy-Item -LiteralPath "$source/REPORT.md" -Destination "$target/REPORT.md"
$src=@(Get-ChildItem $source -File -Recurse|Where-Object Name -ne 'delivery-receipt.json')
$dst=@(Get-ChildItem $target -File -Recurse|Where-Object Name -ne 'delivery-receipt.json')
$sourceBytes=($src|Measure-Object Length -Sum).Sum
$targetBytes=($dst|Measure-Object Length -Sum).Sum
if($src.Count -ne $dst.Count -or $sourceBytes -ne $targetBytes){throw 'Delivery count/size mismatch; inspect without deleting foreign files'}
foreach($file in $src){
    $relative=[IO.Path]::GetRelativePath($source,$file.FullName)
    $copied=Join-Path $target $relative
    if(-not(Test-Path -LiteralPath $copied) -or (Get-Item -LiteralPath $copied).Length -ne $file.Length){throw "Missing/mismatched file: $relative"}
}
$critical=@('REPORT.md','STATUS.md','generated-scope.json','post-gis-own-integrity.json',
    'budget-summary.json','appearance-geometry-audit.json','capture-inputs-audit.json','visual-review.json',
    'before-source/far_field.glb','before-source/far_field.low.glb',
    'after-source/far_field.glb','after-source/far_field.low.glb',
    'after-source/world_edge_far-Low.asset','after-source/world_edge_far-High.asset',
    'reference-photos.json','tests/editmode.xml','tests/gis-final.xml')
foreach($relative in $critical){
    if((Get-FileHash -LiteralPath (Join-Path $source $relative) -Algorithm SHA256).Hash -ne
       (Get-FileHash -LiteralPath (Join-Path $target $relative) -Algorithm SHA256).Hash){throw "SHA mismatch: $relative"}
}
@{round='edge-r5';branch='gpt-edge-r5';report_commit=$reportCommit;files_excluding_receipt=$src.Count;
  bytes_excluding_receipt=$sourceBytes;robocopy_exit_code=$copyCode;verified_critical_sha=$critical.Count;
  report_sha256=(Get-FileHash "$source/REPORT.md" -Algorithm SHA256).Hash;
  verification='Every relative file/length, aggregate count/bytes and critical SHA256';
  source=$source;target=$target;finished=(Get-Date -Format o)}|ConvertTo-Json -Depth 4|Set-Content "$source/delivery-receipt.json"
Copy-Item -LiteralPath "$source/delivery-receipt.json" -Destination "$target/delivery-receipt.json"
git add -f artifacts/edge-r5/STATUS.md artifacts/edge-r5/delivery-receipt.json
git commit -m 'WIP edge r5: verify complete artifact delivery to main'
if($LASTEXITCODE -ne0){throw 'Delivery checkpoint failed'}
if((Get-FileHash "$source/REPORT.md").Hash -ne (Get-FileHash "$target/REPORT.md").Hash){throw 'Report changed'}
Get-Content "$source/delivery-receipt.json"
