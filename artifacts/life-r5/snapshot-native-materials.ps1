param([ValidatePattern('^[a-z0-9-]+$')][string]$Tag='before-editmode')
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((git branch --show-current).Trim() -ne 'gpt-life-r5'){throw 'Wrong branch'}
$source=[IO.Path]::GetFullPath('game/Assets/_Generated/World/bialystok-industrial-c/Materials')
$out=[IO.Path]::GetFullPath("artifacts/life-r5/native-material-backups/$Tag")
if(Test-Path $out){throw 'Snapshot exists; inspect rather than overwrite'}
$files=@(Get-ChildItem -LiteralPath $source -Filter '*.mat' -File)
$manifestPath='Data/Regions/bialystok-industrial-c/generated/world_manifest.json'
$manifest=Get-Content $manifestPath -Raw|ConvertFrom-Json
$required=@($manifest.materials.PSObject.Properties|Where-Object {$_.Value.collision -ne $true}|ForEach-Object {$_.Name})
if(!$required.Count){throw 'Canonical material definitions missing'}
$missing=@($required|Where-Object {!(Test-Path (Join-Path $source "M_$_.mat"))})
if($missing.Count){throw "Missing required native materials: $($missing -join ', ')"}
New-Item -ItemType Directory -Path $out|Out-Null
$rows=@(foreach($file in $files){
 $hash=(Get-FileHash -LiteralPath $file.FullName).Hash
 $copy=Join-Path $out $file.Name
 Copy-Item -LiteralPath $file.FullName -Destination $copy
 if((Get-FileHash -LiteralPath $file.FullName).Hash -ne $hash -or (Get-FileHash -LiteralPath $copy).Hash -ne $hash){throw 'Snapshot changed while copying'}
 @{file=$file.Name;sha=$hash;bytes=$file.Length}
})
@{time=(Get-Date -Format o);source=$source;source_commit=(git rev-parse HEAD).Trim();materials=$rows;
 manifest_sha=(Get-FileHash $manifestPath).Hash;required_materials=$required;missing_required=$missing;
 note='Exact own native bytes for tracing EditMode side effects. Not permission to hide test failures or normalize materials. Any restoration requires explicit diff, reference check, retained raw results and full fresh parity.'}|ConvertTo-Json -Depth 5|Set-Content (Join-Path $out 'snapshot.json')
Write-Output "Saved $($rows.Count) exact native material files to $out"
