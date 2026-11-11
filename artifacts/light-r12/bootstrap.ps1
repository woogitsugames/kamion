$ErrorActionPreference='Stop'
$sourceRoot='C:/Users/matma/Documents/Claude/kamion'
$taskRoot='C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/gpt-light-r12'
Set-Location $taskRoot
& git lfs checkout
foreach($rel in @('Data/raw/derived','Data/raw/cc0','art-source/world/cc0/_raw','art-source/world/megascans','game/Assets/_Generated','art-source/world/materials','Data/photos','game/Library')) {
 $src=Join-Path $sourceRoot $rel; $dst=Join-Path $taskRoot $rel
 if(Test-Path $src) {
  Write-Output "COPY $rel"
  & robocopy $src $dst /E /XJ /R:1 /W:1 /NFL /NDL /NJH /NJS
  if($LASTEXITCODE -gt 7){throw "copy failed: $rel exit=$LASTEXITCODE"}
 } else {Write-Output "SOURCE ABSENT $rel"}
}
foreach($name in @('gugik','osm','refs','mapillary','fab')) {
 $src=Join-Path $sourceRoot "Data/raw/$name"; $dst=Join-Path $taskRoot "Data/raw/$name"
 if((Test-Path $src) -and -not(Test-Path $dst)) {New-Item -ItemType Junction -Path $dst -Target $src | Out-Null}
}
Write-Output 'BOOTSTRAP COMPLETE; junction sources read-only by task policy'
