$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
if((git branch --show-current).Trim() -ne 'gpt-light-r5'){throw 'Wrong round'}
$start=Get-Date
& pwsh "$PSScriptRoot/run-light-batch.ps1" -Jobs artifacts/light-r5/guard-negative.json -Gate3 artifacts/light-r5/qa-cameras.json *> "$PSScriptRoot/guard-negative-wrapper.log"
$actualExit=$LASTEXITCODE
$log=Get-ChildItem -LiteralPath $PSScriptRoot -Filter 'guard-negative.*.log'|Where-Object {$_.LastWriteTime -ge $start}|Sort-Object LastWriteTime -Descending|Select-Object -First 1
if($null -eq $log -or $actualExit -eq 0){throw 'Negative guard unexpectedly accepted or log missing'}
if(-not (Select-String -Path $log.FullName -Pattern 'Stale bake key in QA_cab-dash' -Quiet) -or
   -not (Select-String -Path $log.FullName -SimpleMatch 'LIGHT_QA_RESULT: FAILED' -Quiet) -or
   (Select-String -Path $log.FullName -Pattern 'Shader error|error CS\d+' -Quiet)){
    throw 'Failed for a different reason; stale-key rejection unproven'
}
if(Test-Path "$PSScriptRoot/guard-negative/opaque-grade-proof.json"){throw 'Invalid guard proof persisted'}
@{scope='Actual exported QA camera with Clear whiteClip1.9 deliberately mismatching reviewed1.8 bake; expected failure, not a valid render set';
    rejected=$true;exit=$actualExit;log=$log.Name;sha256=(Get-FileHash -LiteralPath $log.FullName).Hash}|ConvertTo-Json|Set-Content "$PSScriptRoot/guard-negative-result.json" -Encoding utf8
Add-Content "$PSScriptRoot/STATUS.md" 'Negatywny test rzeczywistej kamery QA odrzucił celowo niezgodny whiteClip 1,9 wobec bake 1,8. Przyczyną jest klucz, nie kompilacja shadera; brak ważnego proof. Wyłączenie bootstrapu z bindera nie omija weryfikacji eksportowanego obrazu.'
git add -f artifacts/light-r5/STATUS.md
git commit -m 'WIP light r5: verify actual exported camera rejects stale grade bake'
