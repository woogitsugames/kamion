$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$main='C:\Users\matma\Documents\Claude\kamion'
if($root -ne "$main\.claude\worktrees\gpt-life"){throw 'Wrong workspace'}
Set-Location $root
if((git branch --show-current).Trim() -ne 'gpt-life-r5'){throw 'Wrong branch'}
$folders=@('Data/raw/cc0','art-source/world/cc0/_raw','art-source/world/megascans',
 'game/Assets/_Generated/Truck','game/Assets/_Generated/Trailer')
function Fixture-Hashes {
 $map=[ordered]@{}
 foreach($folder in $folders|Where-Object {$_ -like 'game/*'}) {
  foreach($file in Get-ChildItem -LiteralPath (Join-Path $main $folder) -Recurse -File){
   $rel=[IO.Path]::GetRelativePath($main,$file.FullName)
   $map[$rel]=(Get-FileHash -LiteralPath $file.FullName).Hash
  }
 }
 return $map
}
$before=Fixture-Hashes
foreach($folder in $folders){
 $src=[IO.Path]::GetFullPath((Join-Path $main $folder))
 $dest=[IO.Path]::GetFullPath((Join-Path $root $folder))
 if(!$src.StartsWith($main+'\') -or !$dest.StartsWith($root+'\')){throw 'Unsafe copy path'}
 $tag=$folder.Replace('/','-')
 & robocopy $src $dest /E /R:1 /W:1 /MT:2 /NFL /NDL /NP "/LOG:$PSScriptRoot/copy-$tag.log"
 if($LASTEXITCODE -ge 8){throw "Copy failed: $folder"}
}
$after=Fixture-Hashes
if($before.Count -ne $after.Count){throw 'Main fixture inventory changed during copy'}
foreach($key in $before.Keys){
 if($before[$key] -ne $after[$key]){throw "Main fixture changed during copy: $key"}
 if((Get-FileHash -LiteralPath (Join-Path $root $key)).Hash -ne $after[$key]){throw "Fixture copy differs: $key"}
}
@{source=$main;finished=(Get-Date -Format o);fixtures=$after;count=$after.Count}|ConvertTo-Json -Depth 5|Set-Content "$PSScriptRoot/prepared-fixtures.json"
Add-Content "$PSScriptRoot/STATUS.md" "`nKrok 2: odświeżono raw CC0, źródła CC0/Megascans i natywne Truck/Trailer z main; źródła fixture przed/po kopiowaniu oraz wszystkie kopie zgodne SHA. Nie kopiowano świata z aktywnego main. Następny krok: baseline-gen.ps1 pod jednym heavy."
git add -f artifacts/life-r5
git commit -m 'wip(life): przygotuj źródła i fixture świeżego baseline r5'
if($LASTEXITCODE){throw 'WIP failed'}
