param([Parameter(Mandatory)][int]$WaitFor)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((git branch --show-current).Trim() -ne 'gpt-life-r5'){throw 'Wrong branch; do not mutate another round'}
$running=Get-CimInstance Win32_Process -Filter "ProcessId=$WaitFor"
if($running){
 if($running.Name -ne 'pwsh.exe' -or $running.CommandLine -notmatch ' -NoProfile -File artifacts/life-r5/resume-baseline-capture\.ps1$'){throw 'Not our already-running batch'}
 Wait-Process -Id $WaitFor -ErrorAction SilentlyContinue
}
$ownUnity=@(Get-CimInstance Win32_Process -Filter "Name='Unity.exe'"|Where-Object {$_.CommandLine -match '-projectPath .*gpt-life[\\/]game'})
if($ownUnity.Count){throw 'Own Unity still running; leave it untouched'}
$result=Get-Content artifacts/life-r5/post-baseline-resume-result.json -Raw|ConvertFrom-Json
$validation=if(Test-Path artifacts/life-r5/before-validation.json){Get-Content artifacts/life-r5/before-validation.json -Raw|ConvertFrom-Json}else{$null}
$counts=@{}
if($validation){foreach($p in $validation.PSObject.Properties){$counts[$p.Name]=$p.Value.rows}}
$state=@{time=(Get-Date -Format o);batch_pid=$WaitFor;batch_finished=$true;result=$result;capture_rows=$counts;
 requested_stop=(Test-Path artifacts/life-r5/STOP-DRAINED.json);native_lod_run=$false;
 own_unity_slot=(Test-Path C:/Users/matma/Documents/Claude/kamion/artifacts/locks/unity-slots/gpt-life.slot);
 own_heavy_slot=(Test-Path C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/gpt-life-r5.slot)}
$state|ConvertTo-Json -Depth 8|Set-Content artifacts/life-r5/DRAIN-RESULT.json
git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
Add-Content artifacts/life-r5/STATUS.md ("`nDokończenie tła {0}: batch {1} wyszedł naturalnie; wynik phase={2}, exit={3}, kontrolowane STOP={4}. Faktyczne liczniki capture w DRAIN-RESULT.json; bez diagnostyki LOD, kandydata, nowych testów lub kolejnej rundy. Sloty own Unity={5}, heavy={6}. Nie wznawiać bez polecenia właściciela." -f $state.time,$WaitFor,$result.phase,$result.exit_code,$state.requested_stop,$state.own_unity_slot,$state.own_heavy_slot)
Add-Content artifacts/life-r5/PRZEKAZANIE-LIFE-2026-11-12.md ("`n## Dokończenie pozostawionego batcha`n`nStan z {0}: proces {1} zakończył się naturalnie. Phase: {2}, exit: {3}, kontrolowane zatrzymanie przed LOD: {4}. Dokładne wyniki czterech warunków oraz stan własnych slotów są w DRAIN-RESULT.json. Diagnostyki LOD ani kandydata palet nie uruchomiono. Bez nowych buildów, renderów i testów po tym batchu." -f $state.time,$WaitFor,$result.phase,$result.exit_code,$state.requested_stop)
Add-Content artifacts/life-r5/REPORT.md ("Stan tła po zakończeniu: DRAIN-RESULT.json ({0}); wynik {1}/{2}, STOP={3}; nie kontynuowano rundy." -f $state.time,$result.phase,$result.exit_code,$state.requested_stop)
git add -f artifacts/life-r5/STATUS.md artifacts/life-r5/PRZEKAZANIE-LIFE-2026-11-12.md artifacts/life-r5/REPORT.md artifacts/life-r5/DRAIN-RESULT.json artifacts/life-r5/post-baseline-resume-result.json
if(Test-Path artifacts/life-r5/STOP-DRAINED.json){git add -f artifacts/life-r5/STOP-DRAINED.json}
git commit -m 'wip(life): zapisz naturalne zakończenie batcha i przekazanie'
if($LASTEXITCODE){throw 'Final WIP failed'}
$main='C:/Users/matma/Documents/Claude/kamion/artifacts/life-r5'
robocopy artifacts/life-r5 $main /E /XF REPORT.md finish-stop-console.log /R:0 /W:0 /NFL /NDL /NJH /NJS *> artifacts/life-r5/final-copy.log
if($LASTEXITCODE -gt 7){throw 'Final artifact copy incomplete; inspect final-copy.log'}
Copy-Item artifacts/life-r5/REPORT.md (Join-Path $main 'REPORT.md')
if((Get-FileHash artifacts/life-r5/REPORT.md).Hash -ne (Get-FileHash (Join-Path $main 'REPORT.md')).Hash){throw 'Final report copy mismatch'}
Write-Output "STOP FINALIZED $(Get-Date -Format o)"
