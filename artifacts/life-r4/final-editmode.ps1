$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((git branch --show-current).Trim() -ne 'gpt-life-r4'){throw 'Wrong branch'}
. artifacts/life-r4/assert-selected.ps1
if(Test-Path artifacts/life-r4/final-editmode-result.json){throw 'EditMode evidence already exists'}
if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/unity-slots/gpt-life.slot'){throw 'Own Unity already active'}
$old=@(Get-ChildItem artifacts/tests -Filter 'editmode-*.xml' -ErrorAction SilentlyContinue|ForEach-Object Name)
& pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner gpt-life -StaleHours 1000000 -PollSeconds 1
if($LASTEXITCODE){throw 'Acquire failed'}
$code=1;$details=@{}
try {
 Assert-LifeSelected
 & pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode *> artifacts/life-r4/final-editmode-wrapper.log
 if($LASTEXITCODE){throw 'Inspect EditMode wrapper log'}
 $new=@(Get-ChildItem artifacts/tests -Filter 'editmode-*.xml'|Where-Object Name -notin $old)
 if($new.Count -ne 1){throw 'Cannot identify one new XML'}
 Copy-Item $new[0].FullName artifacts/life-r4/final-editmode.xml
 [xml]$xml=Get-Content $new[0].FullName
 $run=$xml.'test-run'
 if([int]$run.failed -or [int]$run.total -eq 0 -or $run.result -ne 'Passed'){throw 'EditMode XML not Passed'}
 $stamp=$new[0].BaseName.Substring('editmode-'.Length)
 Copy-Item "artifacts/logs/test-editmode-$stamp.log" artifacts/life-r4/final-editmode.log
 $details=@{total=[int]$run.total;passed=[int]$run.passed;failed=[int]$run.failed;skipped=[int]$run.skipped;result=$run.result}
 Assert-LifeSelected
 & pwsh -NoProfile -File artifacts/life-r4/validate-native-materials.ps1 -Tag final-editmode *> artifacts/life-r4/final-editmode-native-materials.log
 if($LASTEXITCODE){throw 'Native materials changed during EditMode'}
 $code=0
} finally {
 & pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner gpt-life
 git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
 $details+=@{exit_code=$code;finished=(Get-Date -Format o);tested_commit=(git rev-parse HEAD).Trim();source_capture=$lifeSelection.source_capture}
 $details|ConvertTo-Json|Set-Content artifacts/life-r4/final-editmode-result.json
 Add-Content artifacts/life-r4/STATUS.md ("`nKońcowy EditMode ({0}) terminalny kod {1}; slot zwolniony i ustawienia cofnięte. Liczby w final-editmode-result.json. Następny krok: odczyt wyniku, końcowy GIS, pary foto i REPORT/kopia." -f (Get-Date -Format o),$code)
 git add -f artifacts/life-r4/STATUS.md artifacts/life-r4/final-editmode-result.json artifacts/life-r4/final-editmode-wrapper.log
 if(Test-Path artifacts/life-r4/final-editmode.xml){git add -f artifacts/life-r4/final-editmode.xml artifacts/life-r4/final-editmode.log}
 git commit -m 'wip(life): zapisz końcowy EditMode kół placowych'
}
if($code){throw 'EditMode failed'}
