$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((git branch --show-current).Trim() -ne 'gpt-life-r3'){throw 'Wrong branch'}
if(!(Get-Content artifacts/life-r3/C-SELECTED.json -Raw|ConvertFrom-Json).selected){throw 'Select C first'}
$proof=Get-Content artifacts/life-r3/after-c-inputs.json -Raw|ConvertFrom-Json
function Assert-Frozen {
 foreach($p in $proof.source_sha.PSObject.Properties){if((Get-FileHash $p.Name).Hash -ne $p.Value){throw "C source changed: $($p.Name)"}}
 if((Get-FileHash art-source/world/props/street_props.glb).Hash -ne $proof.library_sha){throw 'C library changed'}
}
Assert-Frozen
if(Test-Path artifacts/life-r3/final-editmode-result.json){throw 'EditMode evidence exists'}
if(Test-Path C:/Users/matma/Documents/Claude/kamion/artifacts/locks/unity-slots/gpt-life.slot){throw 'Own Unity active'}
$existing=@(Get-ChildItem artifacts/tests -Filter 'editmode-*.xml' -ErrorAction SilentlyContinue|ForEach-Object {$_.Name})
& pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner gpt-life -StaleHours 1000000 -PollSeconds 1
if($LASTEXITCODE){throw 'Acquire failed'}
$code=1;$details=@{}
try {
 & pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode *> artifacts/life-r3/final-editmode-wrapper.log
 if($LASTEXITCODE){throw 'EditMode failed; inspect wrapper log'}
 $new=@(Get-ChildItem artifacts/tests -Filter 'editmode-*.xml'|Where-Object {$_.Name -notin $existing})
 if($new.Count -ne 1){throw 'Cannot identify one fresh EditMode XML'}
 Copy-Item $new[0].FullName artifacts/life-r3/final-editmode.xml
 [xml]$xml=Get-Content $new[0].FullName
 $run=$xml.'test-run'
 if([int]$run.failed -ne 0 -or [int]$run.total -eq 0 -or $run.result -ne 'Passed'){throw 'EditMode XML not Passed'}
 $stamp=$new[0].BaseName.Substring('editmode-'.Length)
 Copy-Item "artifacts/logs/test-editmode-$stamp.log" artifacts/life-r3/final-editmode.log
 $details=@{total=[int]$run.total;passed=[int]$run.passed;failed=[int]$run.failed;skipped=[int]$run.skipped;result=$run.result}
 Assert-Frozen
 & pwsh -NoProfile -File artifacts/life-r3/validate-native-b.ps1 *> artifacts/life-r3/final-editmode-native-materials.log
 if($LASTEXITCODE){throw 'Native materials changed during EditMode'}
 $code=0
} finally {
 & pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner gpt-life
 git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
 $details+=@{exit_code=$code;finished=(Get-Date -Format o);tested_commit=(git rev-parse HEAD);source_capture='after-c-inputs.json'}
 $details|ConvertTo-Json|Set-Content artifacts/life-r3/final-editmode-result.json
 Add-Content artifacts/life-r3/STATUS.md ("`nKońcowy EditMode ({0}) zakończony kodem {1}; slot zwolniony, ustawienia przywrócone. Liczby w final-editmode-result.json. Następny krok: wynik końcowego heavy, oględziny pełnych plansz, ADR/REPORT/kopia i r4." -f (Get-Date -Format o),$code)
 git add -f -- artifacts/life-r3/STATUS.md artifacts/life-r3/final-editmode-result.json artifacts/life-r3/final-editmode-wrapper.log
 if(Test-Path artifacts/life-r3/final-editmode.xml){git add -f -- artifacts/life-r3/final-editmode.xml artifacts/life-r3/final-editmode.log}
 git commit -m 'wip(life): zapisz końcowy EditMode osobówek C'
}
if($code){throw 'EditMode failed'}
