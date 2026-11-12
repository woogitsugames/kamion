param([ValidatePattern('^[a-z0-9-]+$')][string]$Tag='after-a2')
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((git branch --show-current).Trim() -ne 'gpt-life-r4'){throw 'Wrong branch'}
$base=Get-Content artifacts/life-r4/native-baseline-materials.json -Raw|ConvertFrom-Json
$current=@{}
foreach($f in Get-ChildItem game/Assets/_Generated/World/bialystok-industrial-c -Recurse -File -Filter '*.mat'){
 $rel=[IO.Path]::GetRelativePath($PWD,$f.FullName).Replace('\','/')
 $current[$rel]=(Get-FileHash -LiteralPath $f.FullName).Hash
}
$missing=@();$changed=@()
foreach($entry in $base.materials.PSObject.Properties){
 if(!$current.ContainsKey($entry.Name)){$missing+=$entry.Name}
 elseif($current[$entry.Name] -ne $entry.Value){$changed+=$entry.Name}
}
$old=@($base.materials.PSObject.Properties.Name)
$added=@($current.Keys|Where-Object {$_ -notin $old})
$result=@{checked=$base.count;current=$current.Count;missing=$missing;changed=$changed;added=$added;
 pass=(!$missing.Count -and !$changed.Count -and !$added.Count);finished=(Get-Date -Format o);
 note='Actual native material asset bytes; includes bindings, tint, keyword and pass state. No timing/realism claim.'}
$result|ConvertTo-Json -Depth 5|Set-Content "artifacts/life-r4/$Tag-native-materials.json"
$result|ConvertTo-Json -Depth 5|Write-Output
if(!$result.pass){throw 'Native material inventory or bytes changed; inspect before claiming geometry-only'}
