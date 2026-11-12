$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if ((& git branch --show-current).Trim() -ne 'gpt-asphalt-r3') { throw 'Wrong round' }
$resync='e5eb5902'
$sourceChanges=@(& git diff "$resync^1" $resync --name-only -- art-source/world/materials/_src)
if($LASTEXITCODE -ne 0 -or $sourceChanges.Count){throw 'Material sources changed; rebuild them under heavy before World'}
# No material builder source changed in this merge. Confirm every Medium cache entry is newer than its source set.
$root='art-source/world/materials'
$spec=Get-Content "$root/materials_spec.json" -Raw|ConvertFrom-Json
$srcTime=(Get-ChildItem "$root/_src" -Filter '*.py'|Measure-Object LastWriteTimeUtc -Maximum).Maximum
foreach($set in $spec.sets.PSObject.Properties){
 $medium=$set.Value.files.Medium
 if(-not $medium){continue}
 foreach($name in $medium.files){
  $path=Join-Path $root "$($medium.dir)/$name"
  if(-not(Test-Path $path) -or (Get-Item $path).LastWriteTimeUtc -lt $srcTime){throw "Material cache is stale: $path"}
 }
}
$progress=[ordered]@{started_at=(Get-Date -Format o);resync_merge=$resync;material_sources_changed=$false;material_cache_time_guard=$true;complete=$false;world_exit=$null;manifest_sha256=$null}
$progress|ConvertTo-Json|Set-Content artifacts/asphalt-r3/baseline-producer-progress.json
& pwsh artifacts/asphalt-r3/run-heavy.ps1 -Stage World -Label baseline
$progress.world_exit=$LASTEXITCODE
if($progress.world_exit -eq 0){
 if(Select-String -Path artifacts/asphalt-r3/baseline-World.log -SimpleMatch 'fallback=True' -Quiet){throw 'World fallback present'}
 $progress.manifest_sha256=(Get-FileHash Data/Regions/bialystok-industrial-c/generated/world_manifest.json).Hash
 $progress.complete=$true
}
$progress.finished_at=Get-Date -Format o
$progress|ConvertTo-Json|Set-Content artifacts/asphalt-r3/baseline-producer-progress.json
Add-Content artifacts/asphalt-r3/STATUS.md "$(Get-Date -Format o): Regeneracja World po ADR0131 exit=$($progress.world_exit), complete=$($progress.complete). Cache materiałów zachowany: merge nie zmienił żadnego _src, wszystkie Medium PNG świeższe od źródeł. Receipt wiąże wynik z SHA manifestu; dawne wpisy STATUS nie stanowią dowodu świeżego sukcesu."
git add -f artifacts/asphalt-r3/STATUS.md artifacts/asphalt-r3/baseline-producer-progress.json
git commit -q -m 'wip(asphalt): checkpoint post-0131 canonical producer receipt'
exit $progress.world_exit
