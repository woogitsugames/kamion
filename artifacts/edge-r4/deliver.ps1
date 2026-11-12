$ErrorActionPreference='Stop'
$source=(Resolve-Path $PSScriptRoot).Path
$root=(Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $root
$round=Split-Path $source -Leaf
if($round -ne 'edge-r4' -or (git branch --show-current).Trim() -ne 'gpt-edge-r4'){throw 'Wrong round'}
if(-not(Test-Path "$source/post-gis.complete")){throw 'Post-GIS checks not complete'}
if(-not(Test-Path "$source/gis-final-receipt.json")){throw 'Missing final GIS result'}
if(@(Get-Content "$source/REPORT.md").Count -gt 20){throw 'Report too long'}
$target='C:/Users/matma/Documents/Claude/kamion/artifacts/edge-r4'
$log=Join-Path $root 'artifacts/edge-r4-delivery.log'
$reportCommit=(git rev-parse HEAD).Trim()
& robocopy $source $target /E /XJ /MT:1 /R:1 /W:1 /XF REPORT.md delivery-receipt.json /NFL /NDL /NP "/LOG:$log"
$copyCode=$LASTEXITCODE
if($copyCode -ge 8){throw "Robocopy failed: $copyCode"}
Copy-Item -LiteralPath $log -Destination "$source/robocopy-delivery.log"
Copy-Item -LiteralPath $log -Destination "$target/robocopy-delivery.log"
Add-Content "$source/STATUS.md" 'Krok 48: pełny robocopy r4 zakończony bez błędu; REPORT opublikowany dopiero po plikach dowodowych. Weryfikacja obejmuje każdy względny plik i rozmiar oraz SHA raportu i kluczowych dowodów. Szczegóły i końcowe liczby w delivery-receipt.json. Bez commitowania do main, push i merge do main; następna czynność to gałąź r5 i merge main do niej.'
Copy-Item -LiteralPath "$source/STATUS.md" -Destination "$target/STATUS.md"
Copy-Item -LiteralPath "$source/REPORT.md" -Destination "$target/REPORT.md"
$src=@(Get-ChildItem $source -File -Recurse|Where-Object Name -ne 'delivery-receipt.json')
$dst=@(Get-ChildItem $target -File -Recurse|Where-Object Name -ne 'delivery-receipt.json')
$sourceBytes=($src|Measure-Object Length -Sum).Sum
$targetBytes=($dst|Measure-Object Length -Sum).Sum
if($src.Count -ne $dst.Count -or $sourceBytes -ne $targetBytes){throw 'Delivery count/size mismatch'}
foreach($file in $src){
    $relative=[IO.Path]::GetRelativePath($source,$file.FullName)
    $copied=Join-Path $target $relative
    if(-not(Test-Path -LiteralPath $copied) -or (Get-Item -LiteralPath $copied).Length -ne $file.Length){throw "Missing/mismatched file: $relative"}
}
$critical=@('REPORT.md','STATUS.md','post-gis-scope.json','cloud-cutoff-measurement.json','baseline-camera-inventory.json',
    'before-source/world_edge.asset','before-source/far_field.glb','before-source/far_field.low.glb',
    'reference-photos.json','tests/full-editmode.xml')
foreach($relative in $critical){
    if((Get-FileHash -LiteralPath (Join-Path $source $relative) -Algorithm SHA256).Hash -ne
       (Get-FileHash -LiteralPath (Join-Path $target $relative) -Algorithm SHA256).Hash){throw "SHA mismatch: $relative"}
}
@{round=$round;branch='gpt-edge-r4';report_commit=$reportCommit;files_excluding_receipt=$src.Count;
  bytes_excluding_receipt=$sourceBytes;robocopy_exit_code=$copyCode;verified_critical_sha=$critical.Count;
  report_sha256=(Get-FileHash "$source/REPORT.md" -Algorithm SHA256).Hash;
  verification='Every relative file and length, aggregate count/bytes, ten critical hashes';
  source=$source;target=$target;finished=(Get-Date -Format o)}|ConvertTo-Json -Depth 4|Set-Content "$source/delivery-receipt.json"
Copy-Item -LiteralPath "$source/delivery-receipt.json" -Destination "$target/delivery-receipt.json"
git add -f artifacts/edge-r4/STATUS.md artifacts/edge-r4/delivery-receipt.json
git commit -m 'WIP edge r4: verify complete artifact delivery to main'
if($LASTEXITCODE -ne 0){throw 'Delivery checkpoint failed'}
if((Get-FileHash "$source/REPORT.md").Hash -ne (Get-FileHash "$target/REPORT.md").Hash){throw 'Report changed'}
Get-Content "$source/delivery-receipt.json"
