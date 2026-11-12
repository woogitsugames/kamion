$ErrorActionPreference='Stop'
$source=[IO.Path]::GetFullPath($PSScriptRoot)
$expected='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-life\artifacts\life-r4'
$target='C:\Users\matma\Documents\Claude\kamion\artifacts\life-r4'
if($source -ne $expected){throw 'Unexpected source'}
Set-Location ([IO.Path]::GetFullPath((Join-Path $source '../..')))
if((git branch --show-current).Trim() -ne 'gpt-life-r4'){throw 'Wrong branch'}
$done=Get-Content "$source/final-heavy-result.json" -Raw|ConvertFrom-Json
if($done.phase -ne 'complete' -or $done.exit_code -ne 0){throw 'Final heavy not complete'}
$edit=Get-Content "$source/final-editmode-result.json" -Raw|ConvertFrom-Json
if($edit.failed -ne 0 -or $edit.result -ne 'Passed'){throw 'EditMode tests not green'}
if($edit.exit_code -ne 0 -and !((Get-Content artifacts/life-r4/final-editmode-restored.json -Raw|ConvertFrom-Json).accepted)){throw 'EditMode cleanup not accepted'}
$report=Join-Path $source 'REPORT.md'
if(!(Test-Path $report)){throw 'Missing final report'}
if(@(Get-Content $report).Count -gt 20){throw 'REPORT exceeds 20 lines'}
if(Test-Path "$target/REPORT.md"){throw 'Report already published; inspect before any repeat'}
$tracked=git status --porcelain
if($tracked){throw 'Commit final evidence before publication'}
$log=Join-Path (Split-Path $source) 'life-r4-final-copy.log'
& robocopy $source $target /E /R:1 /W:1 /MT:2 /XD .cache __pycache__ /XF REPORT.md /NFL /NDL /NP "/LOG:$log"
$rc=$LASTEXITCODE
if($rc -ge 8){throw "Robocopy failed $rc"}
$files=Get-ChildItem -LiteralPath $source -Recurse -File|Where-Object {
 $_.Name -ne 'REPORT.md' -and $_.FullName -notmatch '[\\/](?:\.cache|__pycache__)[\\/]'
}
$bytes=0L
foreach($file in $files){
 $rel=[IO.Path]::GetRelativePath($source,$file.FullName)
 $dest=Join-Path $target $rel
 if(!(Test-Path -LiteralPath $dest)){throw "Missing copied file: $rel"}
 if((Get-Item -LiteralPath $dest).Length -ne $file.Length){throw "Size differs: $rel"}
 $bytes+=$file.Length
}
$critical=@('final-heavy-result.json','final-gis.log','final-editmode.xml','after-a2-inputs.json',
 'a2-all-camera-budget.json','final-editmode-restored.json','final-heavy-native-materials.json',
 'refs/sbs-yard-rim-a2.jpg','refs/sbs-wheel-detail-a2.jpg','STATUS.md','AUTHOR-REVIEW.md','NEXT-R5.md')
$hashes=@{}
foreach($rel in $critical){
 $a=(Get-FileHash -LiteralPath (Join-Path $source $rel)).Hash
 $b=(Get-FileHash -LiteralPath (Join-Path $target $rel)).Hash
 if($a -ne $b){throw "Hash differs: $rel"}
 $hashes[$rel]=$a
}
$receipt=@{finished=(Get-Date -Format o);source=$source;target=$target;files=$files.Count;bytes=$bytes;
 robocopy_exit=$rc;critical_sha=$hashes;commit=(git rev-parse HEAD).Trim();report_published_last=$true}
$receipt|ConvertTo-Json -Depth 6|Set-Content "$source/COPY-RECEIPT.json"
Copy-Item -LiteralPath "$source/COPY-RECEIPT.json" -Destination "$target/COPY-RECEIPT.json"
Copy-Item -LiteralPath $report -Destination "$target/REPORT.md"
if((Get-FileHash $report).Hash -ne (Get-FileHash "$target/REPORT.md").Hash){throw 'Report hash differs'}
Write-Output ($receipt|ConvertTo-Json -Depth 6)
